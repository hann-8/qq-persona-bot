import sqlite3


class TaskStore:
    def __init__(self,path):
        path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS tasks (message_key TEXT PRIMARY KEY, trace TEXT, status TEXT, updated REAL)')
        with self.db:self.db.execute("UPDATE tasks SET status='unknown' WHERE status IN ('accepted','running')")

    def accept(self,key,trace):
        with self.db:
            cursor=self.db.execute("INSERT OR IGNORE INTO tasks VALUES (?,?,'accepted',unixepoch())",(key,trace))
        return cursor.rowcount==1

    def set(self,key,status):
        if status not in ('running','completed','failed','send_unknown','unknown'):raise ValueError('Invalid task state')
        with self.db:self.db.execute('UPDATE tasks SET status=?,updated=unixepoch() WHERE message_key=?',(status,key))

    def close(self):self.db.close()
