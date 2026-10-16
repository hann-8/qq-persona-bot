import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.session_queue import SessionCoordinator,SessionError,trim_history
from qqbot_gateway.task_store import TaskStore


class HistoryTests(unittest.TestCase):
    def test_serialized_tool_turn_is_not_reused(self):
        history=[{'role':'user','content':'good'}, {'role':'assistant','content':'answer'},
                 {'role':'user','content':'remember'},
                 {'role':'assistant','content':'<｜｜DSML｜｜ invoke name="Write">private path'},
                 {'role':'user','content':'unfinished'}]
        self.assertEqual(trim_history(history),history[:2])

    def test_complete_turns_and_character_budget(self):
        history=[]
        for i in range(10):history.extend([{'role':'user','content':str(i)*3},{'role':'assistant','content':'answer'}])
        kept=trim_history(history,turns=7)
        self.assertEqual(len(kept),14);self.assertEqual(kept[0]['content'],'333')
        kept=trim_history(history,turns=7,char_limit=10)
        self.assertEqual(len(kept),2);self.assertEqual(kept[0]['content'],'999')

    def test_orphan_and_tool_content_dropped(self):
        history=[{'role':'system','content':'old system'}, {'role':'assistant','content':'orphan'},
                 {'role':'user','content':'question'},{'role':'assistant','content':[{'type':'text','text':'answer'}]},
                 {'role':'user','content':'unfinished'}]
        self.assertEqual(trim_history(history),[{'role':'user','content':'question'},{'role':'assistant','content':'answer'}])

    def test_task_dedup_and_restart_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'tasks.sqlite';store=TaskStore(p)
            self.assertTrue(store.accept('message','trace'));store.set('message','running')
            self.assertFalse(store.accept('message','trace2'));store.close()
            store=TaskStore(p)
            self.assertEqual(store.db.execute('SELECT status FROM tasks').fetchone()[0],'unknown')
            self.assertFalse(store.accept('message','trace3'));store.close()


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_scope_fifo_other_scopes_independent(self):
        queue=SessionCoordinator(cooldown=0)
        first=await queue.acquire('group_A/user_A')
        second=asyncio.create_task(queue.acquire('group_A/user_A'))
        third=asyncio.create_task(queue.acquire('group_A/user_A'))
        await asyncio.sleep(0)
        other=await queue.acquire('group_A/user_B');other.release()
        different=await queue.acquire('group_B/user_A');different.release()
        self.assertFalse(second.done());self.assertFalse(third.done())
        first.release();second_lease=await second;self.assertFalse(third.done())
        second_lease.release();(await third).release()

    async def test_cooldown_and_notice_throttle(self):
        clock=[0.0];queue=SessionCoordinator(clock=lambda:clock[0])
        (await queue.acquire('session')).release()
        for expected in (True,False):
            with self.assertRaises(SessionError) as result:await queue.acquire('session')
            self.assertEqual(result.exception.code,'COOLDOWN');self.assertEqual(result.exception.notify,expected)
        clock[0]=5;(await queue.acquire('session')).release()

    async def test_queue_full_timeout_and_cancellation_release(self):
        queue=SessionCoordinator(cooldown=0,limit=1,timeout=.02)
        first=await queue.acquire('session')
        second=asyncio.create_task(queue.acquire('session'));await asyncio.sleep(0)
        with self.assertRaises(SessionError) as error:await queue.acquire('session')
        self.assertEqual(error.exception.code,'SESSION_QUEUE_FULL')
        with self.assertRaises(SessionError) as error:await second
        self.assertEqual(error.exception.code,'SESSION_QUEUE_TIMEOUT')
        first.release();lease=await queue.acquire('session');lease.release()

    async def test_cancelled_waiter_does_not_steal_next_slot(self):
        queue=SessionCoordinator(cooldown=0)
        first=await queue.acquire('session')
        cancelled=asyncio.create_task(queue.acquire('session'));await asyncio.sleep(0)
        cancelled.cancel();await asyncio.gather(cancelled,return_exceptions=True)
        next_task=asyncio.create_task(queue.acquire('session'));await asyncio.sleep(0)
        first.release();(await asyncio.wait_for(next_task,1)).release()


if __name__=='__main__':unittest.main()
