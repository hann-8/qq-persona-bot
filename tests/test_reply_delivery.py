import asyncio
import json
from pathlib import Path
import sys
import tempfile
import sqlite3
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.reply_delivery import ReplyDelivery, GroupDeliveryQueue, DeliveryStopped
from qqbot_gateway.reply_plan import DEFAULTS, ReplyPlan
from qqbot_gateway.task_store import TaskStore


class History:
    def __init__(self,history):self.history=history;self.writes=0
    async def get_conversation(self,umo,cid):return SimpleNamespace(history=json.dumps(self.history))
    async def update_conversation(self,umo,cid,history):self.history=history;self.writes+=1


class DeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'tasks.sqlite'
        self.store=TaskStore(self.path)
        self.plan=ReplyPlan('chat',('a','b','c'),'a\nb\nc')
        self.before=[{'role':'user','content':'old'},{'role':'assistant','content':'old answer'}]
        self.expected=self.before+[{'role':'user','content':'new'},{'role':'assistant','content':self.plan.canonical_text}]
    async def asyncTearDown(self):self.store.close();self.temp.cleanup()
    def prepare(self,key='key'):
        self.store.accept(key,'trace')
        return self.store.prepare_delivery(key,'umo','cid','response',self.plan,self.before,self.expected)

    async def test_recovery_all_crash_positions_and_prefix(self):
        for current in (self.before,self.expected):
            for sent in range(4):
                key=f'{len(current)}-{sent}';self.prepare(key)
                for i in range(sent):
                    self.store.begin_part(key,i);self.store.part_result(key,i,'sent',str(i+1))
                if sent<3:self.store.begin_part(key,sent) # crash with send intent, ACK unknown
                history=History(current)
                await self.store.repair_delivery(key,history)
                want=current if current==self.before else self.expected[:-1]+([{'role':'assistant','content':'\n'.join(self.plan.bubbles[:sent])}] if sent else [])
                self.assertEqual(history.history,want)
                self.assertEqual(self.store.delivery(key)['repair'],'repaired')
                await self.store.repair_delivery(key,history)
                self.assertEqual(history.history,want)

    async def test_repair_cas_mismatch_quarantines_without_deletion(self):
        self.prepare();history=History(self.expected+[{'role':'user','content':'later'}])
        original=list(history.history)
        await self.store.recover_deliveries(history)
        self.assertEqual(history.history,original);self.assertEqual(history.writes,0)
        self.assertTrue(self.store.quarantined('umo','cid'))
        self.assertFalse(self.store.quarantined('other','cid'))

    async def test_old_tasks_schema_and_bot_only_tail_record(self):
        legacy=Path(self.temp.name)/'legacy.sqlite'
        with sqlite3.connect(legacy) as db:
            db.execute('CREATE TABLE tasks (message_key TEXT PRIMARY KEY,trace TEXT,status TEXT,updated REAL)')
            db.execute("INSERT INTO tasks VALUES ('old','old','completed',1)")
        db.close()
        store=TaskStore(legacy)
        try:self.assertEqual(store.db.execute('SELECT status FROM tasks').fetchone()[0],'completed')
        finally:store.close()
        self.prepare()
        identity=self.store.delivery('key')['tail_identity']
        self.assertNotIn('old answer',identity);self.assertNotIn('new',identity)

    async def test_already_repaired_before_marking_ledger_is_idempotent(self):
        self.prepare();self.store.begin_part('key',0);self.store.part_result('key',0,'sent','1')
        history=History(self.expected[:-1]+[{'role':'assistant','content':'a'}])
        await self.store.repair_delivery('key',history)
        self.assertEqual(history.writes,0)
        self.assertEqual(self.store.delivery('key')['repair'],'repaired')

    async def test_ack_duplicate_and_restart_do_not_retry(self):
        self.assertTrue(self.prepare());self.assertFalse(self.prepare())
        self.store.begin_part('key',0);self.store.part_result('key',0,'sent','99')
        self.assertFalse(self.store.begin_part('key',0))
        self.store.begin_part('key',1)
        self.assertEqual(self.store.part_result('key',1,'sent','99'),'unknown')
        self.store.close();self.store=TaskStore(self.path)
        history=History(self.expected);await self.store.recover_deliveries(history)
        self.assertEqual(history.history[-1]['content'],'a')
        self.assertEqual(self.store.parts('key')[1][1],'unknown')
        self.assertFalse(self.store.accept('key','new trace'))

    async def test_queue_bound_timeout_cancel_and_serial_order(self):
        queue=GroupDeliveryQueue(timeout=.03)
        async with queue.hold('g',lambda:True):
            async def waiting():
                async with queue.hold('g',lambda:True):pass
            one=asyncio.create_task(waiting());two=asyncio.create_task(waiting())
            await asyncio.sleep(.005)
            with self.assertRaises(DeliveryStopped):
                async with queue.hold('g',lambda:True):pass
            result=await asyncio.gather(one,two,return_exceptions=True)
            self.assertTrue(all(isinstance(x,TimeoutError) for x in result))
        self.assertEqual(queue.groups,{})
        async with queue.hold('g',lambda:True):
            async with queue.hold('another-group',lambda:True):pass
            flag={'allowed':True}
            async def stopped_wait():
                async with queue.hold('g',lambda:flag['allowed']):pass
            queue.timeout=1
            task=asyncio.create_task(stopped_wait());await asyncio.sleep(.005)
            start=time.monotonic();flag['allowed']=False
            result=await asyncio.gather(task,return_exceptions=True)
            self.assertIsInstance(result[0],DeliveryStopped)
            self.assertLess(time.monotonic()-start,.3)
        log=[]
        async def turn(name,group):
            async with queue.hold(group,lambda:True):
                log.append(name+'1');await asyncio.sleep(.005);log.append(name+'2')
        await asyncio.gather(turn('a','g'),turn('b','g'))
        self.assertEqual(log,['a1','a2','b1','b2'])
        async with queue.hold('g',lambda:True):
            task=asyncio.create_task(waiting());await asyncio.sleep(.001);task.cancel()
            await asyncio.gather(task,return_exceptions=True)
        self.assertEqual(queue.groups,{})


if __name__=='__main__':unittest.main()
