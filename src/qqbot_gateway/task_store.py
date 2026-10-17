import sqlite3
import json
from .reply_plan import digest


def history_shape(history):
    """Compare text histories across SDK string/part representations, fail closed on tools."""
    result=[]
    for item in history:
        role=item.get('role')
        if role == 'system':continue
        if role not in ('user','assistant'):raise ValueError('Non-text history')
        content=item.get('content')
        if isinstance(content,list):
            if any(not isinstance(p,dict) or p.get('type')!='text' for p in content):
                raise ValueError('Non-text history')
            content=''.join(p['text'] for p in content)
        if not isinstance(content,str):raise ValueError('Non-text history')
        result.append({'role':role,'content':content})
    return result


def history_digest(history):
    return digest(json.dumps(history_shape(history),ensure_ascii=False,separators=(',',':')))


class TaskStore:
    def __init__(self,path):
        path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS tasks (message_key TEXT PRIMARY KEY, trace TEXT, status TEXT, updated REAL)')
        self.db.execute('''CREATE TABLE IF NOT EXISTS delivery (
            message_key TEXT PRIMARY KEY, umo TEXT NOT NULL, cid TEXT NOT NULL,
            response_id TEXT NOT NULL, content_sha256 TEXT NOT NULL, bubbles TEXT NOT NULL,
            before_sha256 TEXT NOT NULL, expected_sha256 TEXT NOT NULL, tail_identity TEXT NOT NULL,
            state TEXT NOT NULL, repair TEXT NOT NULL DEFAULT 'pending', reason TEXT)''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS delivery_part (
            message_key TEXT NOT NULL, part INTEGER NOT NULL, state TEXT NOT NULL,
            message_id TEXT, PRIMARY KEY(message_key,part))''')
        with self.db:self.db.execute("UPDATE tasks SET status='unknown' WHERE status IN ('accepted','running')")

    def accept(self,key,trace):
        with self.db:
            cursor=self.db.execute("INSERT OR IGNORE INTO tasks VALUES (?,?,'accepted',unixepoch())",(key,trace))
        return cursor.rowcount==1

    def set(self,key,status):
        if status not in ('running','completed','failed','send_unknown','unknown'):raise ValueError('Invalid task state')
        with self.db:self.db.execute('UPDATE tasks SET status=?,updated=unixepoch() WHERE message_key=?',(status,key))

    def prepare_delivery(self,key,umo,cid,response_id,plan,before,expected):
        shape=history_shape(expected)
        if (len(shape)<2 or shape[-2]['role']!='user' or shape[-1]['role']!='assistant' or
                shape[-1]['content']!=plan.canonical_text or history_digest(expected[:-2])!=history_digest(before)):
            raise ValueError('Unrecognized model/history tail')
        # Retain only bot output and tail hashes here, not a second copy of private user history.
        confirmed_hashes=[history_digest(expected[:-1])]
        for count in range(1,len(plan.bubbles)+1):
            assistant=dict(expected[-1]);assistant['content']='\n'.join(plan.bubbles[:count])
            confirmed_hashes.append(history_digest(expected[:-1]+[assistant]))
        with self.db:
            cursor=self.db.execute('INSERT OR IGNORE INTO delivery VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (key,umo,cid,response_id,digest(plan.canonical_text),json.dumps(plan.bubbles,ensure_ascii=False),
                 history_digest(before),history_digest(expected),json.dumps({'confirmed_hashes':confirmed_hashes}),
                 'prepared','pending',plan.fallback_reason))
            if cursor.rowcount:
                self.db.executemany('INSERT INTO delivery_part VALUES (?, ?, ?, NULL)',
                                    [(key,i,'prepared') for i in range(len(plan.bubbles))])
        return bool(cursor.rowcount)

    def delivery(self,key):
        cur=self.db.execute('SELECT * FROM delivery WHERE message_key=?',(key,))
        row=cur.fetchone()
        return dict(zip([c[0] for c in cur.description],row)) if row else None

    def prepare_group_delivery(self,key,group,epoch,response_id,plan,snapshot_digest,seq_range):
        # cid sentinel separates RAM targets from personal repair. No human body persists.
        identity=json.dumps(dict(snapshot_digest=snapshot_digest,seq_range=seq_range,epoch=epoch))
        with self.db:
            cur=self.db.execute('INSERT OR IGNORE INTO delivery VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (key,'group:'+group,'@ram',response_id,digest(plan.canonical_text),json.dumps(plan.bubbles,ensure_ascii=False),
                 snapshot_digest,snapshot_digest,identity,'prepared','pending',plan.fallback_reason))
            if cur.rowcount:self.db.executemany('INSERT INTO delivery_part VALUES (?,?,?,NULL)',[(key,i,'prepared') for i in range(len(plan.bubbles))])
        return bool(cur.rowcount)

    def group_blocked(self,group):
        return bool(self.db.execute("SELECT 1 FROM delivery WHERE umo=? AND cid='@ram' AND state='unknown' AND repair!='operator_reviewed'",('group:'+group,)).fetchone())

    def review_group(self,group):
        with self.db:self.db.execute("UPDATE delivery SET repair='operator_reviewed' WHERE umo=? AND cid='@ram' AND state='unknown'",('group:'+group,))

    def finish_group(self,key):
        self.finish_delivery(key)
        with self.db:self.db.execute("UPDATE delivery SET repair='ram_discarded' WHERE message_key=? AND cid='@ram'",(key,))

    def parts(self,key):
        return self.db.execute('SELECT part,state,message_id FROM delivery_part WHERE message_key=? ORDER BY part',(key,)).fetchall()

    def begin_part(self,key,index):
        with self.db:
            cur=self.db.execute("UPDATE delivery_part SET state='sending' WHERE message_key=? AND part=? AND state='prepared'",(key,index))
            if cur.rowcount:self.db.execute("UPDATE delivery SET state='sending' WHERE message_key=?",(key,))
        return bool(cur.rowcount)

    def part_result(self,key,index,state,message_id=None):
        if state not in ('sent','failed','unknown'):raise ValueError('Invalid part state')
        with self.db:
            if state=='sent' and self.db.execute('SELECT 1 FROM delivery_part WHERE message_key=? AND message_id=?',(key,str(message_id))).fetchone():
                state,message_id='unknown',None
            self.db.execute("UPDATE delivery_part SET state=?,message_id=? WHERE message_key=? AND part=? AND state='sending'",
                            (state,str(message_id) if message_id is not None else None,key,index))
        return state

    def finish_delivery(self,key,reason=None):
        parts=self.parts(key)
        complete=bool(parts) and all(state=='sent' for _,state,_ in parts)
        state='sent' if complete else ('unknown' if any(s in ('sending','unknown','sent') for _,s,_ in parts) else 'failed')
        with self.db:
            self.db.execute("UPDATE delivery_part SET state='unknown' WHERE message_key=? AND state='sending'",(key,))
            self.db.execute('UPDATE delivery SET state=?,reason=COALESCE(?,reason) WHERE message_key=?',(state,reason,key))
        self.set(key,'completed' if complete else ('send_unknown' if state=='unknown' else 'failed'))

    def pending_deliveries(self):
        return [row[0] for row in self.db.execute("SELECT message_key FROM delivery WHERE repair='pending'")]

    def quarantined(self,umo,cid):
        return bool(self.db.execute("SELECT 1 FROM delivery WHERE umo=? AND cid=? AND repair IN ('pending','history_repair_required')",(umo,cid)).fetchone())

    async def repair_delivery(self,key,manager):
        row=self.delivery(key)
        if not row or row['repair']!='pending':return
        self.finish_delivery(key)
        try:
            conv=await manager.get_conversation(row['umo'],row['cid'])
            if conv is None:raise ValueError('Missing conversation')
            current=json.loads(conv.history or '[]')
            identity=json.loads(row['tail_identity'])
            parts=self.parts(key); bubbles=json.loads(row['bubbles'])
            confirmed=[]
            for index,state,_ in parts:
                if state!='sent':break
                confirmed.append(bubbles[index])
            current_hash=history_digest(current)
            if current_hash==row['expected_sha256']:
                corrected=current[:-1]
                if confirmed:
                    assistant=dict(current[-1]);assistant['content']='\n'.join(confirmed)
                    corrected=corrected+[assistant]
                await manager.update_conversation(row['umo'],row['cid'],history=corrected)
            elif current_hash not in (row['before_sha256'],identity['confirmed_hashes'][len(confirmed)]):
                raise ValueError('History tail mismatch')
            repair='repaired'
        except Exception:
            repair='history_repair_required'
        with self.db:self.db.execute('UPDATE delivery SET repair=? WHERE message_key=?',(repair,key))
        if repair!='repaired':self.set(key,'send_unknown')

    async def recover_deliveries(self,manager):
        for key in self.pending_deliveries():
            if self.delivery(key)['cid']=='@ram':self.finish_group(key)
            else:await self.repair_delivery(key,manager)

    def close(self):self.db.close()
