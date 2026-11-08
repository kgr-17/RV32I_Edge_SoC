"""Check independent regression bound, complete evidence and failure retention."""
import threading
import time
import unittest
from unittest import mock
import verify


class RegressionDispatchTests(unittest.TestCase):
    def test_all_targets_join_in_order_with_two_worker_ceiling(self):
        lock=threading.Lock();activity={'live':0,'peak':0,'seen':[]}
        def run(argv,timeout_seconds):
            with lock:
                activity['live']+=1;activity['peak']=max(activity['peak'],activity['live']);activity['seen'].append(argv[0])
            time.sleep(0.01 if argv[0]=='0' else 0.005)
            with lock:activity['live']-=1
            if argv[0]=='2':raise OSError('expected fixture failure')
            return dict(argv=argv,timeout_seconds=timeout_seconds,status='NOT RUN' if argv[0]=='3' else 'PASS',exit_code=125 if argv[0]=='3' else 0)
        commands=[[str(n)] for n in range(7)]
        emitted=[]
        with mock.patch.object(verify.harness,'run',side_effect=run):records=verify.run_commands(commands,600,True,on_record=emitted.append)
        self.assertEqual([r['argv'] for r in records],commands);self.assertCountEqual(activity['seen'],[str(n) for n in range(7)])
        self.assertEqual(activity['live'],0);self.assertEqual(activity['peak'],2)
        self.assertEqual(records[2]['status'],'FAIL');self.assertEqual(records[3]['status'],'NOT RUN')
        self.assertEqual(sorted(r['registered_command_index'] for r in emitted),list(range(7)))
        self.assertTrue(all(r['timeout_seconds']==600 for r in records))
    def test_ordinary_target_dispatch_stays_sequential(self):
        commands=[['one'],['two']]
        with mock.patch.object(verify.harness,'run',side_effect=lambda argv,**kwargs:argv) as run:
            self.assertEqual(verify.run_commands(commands,300),commands)
        self.assertEqual(run.call_args_list,[mock.call(['one'],timeout_seconds=300),mock.call(['two'],timeout_seconds=300)])


if __name__=='__main__':unittest.main(verbosity=2)
