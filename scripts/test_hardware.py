"""Independent negative policy checks; fixtures are never physical evidence."""
import copy
from pathlib import Path
import tempfile
import tkinter
import unittest
from unittest import mock
import hardware
import harness
import hardware_evidence


class HardwarePolicyTests(unittest.TestCase):
    def setUp(self):
        self.target='localhost:3121/xilinx_tcf/Digilent/210183B03B59A'
        self.inv={'status':'PASS','targets':[self.target],
            'devices':[{'target':self.target,'name':'xc7a35t_0','part':'xc7a35t','idcode':'fixture'}],
            'ports':{'serial_ports':[{'DeviceID':'COM3','PNPDeviceID':'FTDIBUS\\VID_0403+PID_6010+210183B03B59B\\0000'}],
                'usb_devices':[{'InstanceId':'USB\\VID_0403&PID_6010\\210183B03B59'}], 'port_names':['COM3']}}
    def test_separate_interfaces_require_shared_present_parent(self):
        self.assertEqual(hardware.select_device(self.inv,self.target,'xc7a35t_0','COM3')['part'],'xc7a35t')
        for field,value in [('usb_devices',[]),('port_names',[]),('serial_ports',[{'DeviceID':'COM3','PNPDeviceID':'FTDIBUS\\VID_0403+PID_6010+OTHERB\\0000'}])]:
            inv=copy.deepcopy(self.inv);inv['ports'][field]=value
            with self.assertRaises(ValueError):hardware.select_device(inv,self.target,'xc7a35t_0','COM3')
    def test_ambiguous_target_part_port_remote_and_interface_a_rejected(self):
        for change in ('multiple','wrong_part','wrong_device','remote','wrong_com','interface_a'):
            inv=copy.deepcopy(self.inv);target=self.target;device='xc7a35t_0';com='COM3'
            if change=='multiple':inv['targets']*=2
            if change=='wrong_part':inv['devices'][0]['part']='xc7a100t'
            if change=='wrong_device':device='xc7a35t_1'
            if change=='remote':target='remote:3121/Digilent/210183B03B59A'
            if change=='wrong_com':com='COM4'
            if change=='interface_a':inv['ports']['serial_ports'][0]['PNPDeviceID']=inv['ports']['serial_ports'][0]['PNPDeviceID'].replace('59B','59A')
            with self.subTest(change=change),self.assertRaises(ValueError):hardware.select_device(inv,target,device,com)
    def test_diagnostics_and_nonzero_cannot_pass_marker(self):
        r={'status':'PASS','exit_code':0,'stdout':'DONE\n','stderr':''}
        self.assertTrue(hardware.native_ok(r,'DONE'))
        for change in ({'exit_code':1},{'stdout':'DONE\nWARNING: bad'},{'stderr':'CRITICAL WARNING: bad'},{'stdout':'DONE\nDONE\n'},{'status':'TIMEOUT'}):
            bad=dict(r,**change);self.assertFalse(hardware.native_ok(bad,'DONE'))
    def test_inventory_strict_schema(self):
        self.assertEqual(hardware.parse_inventory(''),([],[]))
        for bad in ('garbage','target\ta\nunknown\tx','target\ta\ntarget\ta'):
            with self.assertRaises(ValueError):hardware.parse_inventory(bad)
    def test_physical_uart_requires_exact_frame_and_matching_timestamped_events(self):
        e=[{'elapsed_ms':5,'utc':'2026-11-22T01:00:00+00:00','hex':'49525120504153530d0a'}]
        hardware_evidence.validate_uart(b'IRQ PASS\r\n',e,60)
        for raw in (b'',b'IRQ FAIL\r\n',b'IRQ PASS\n',b'IRQ PASS\r\nIRQ PASS\r\n',b'garbageIRQ PASS\r\n'):
            with self.assertRaises(ValueError):hardware_evidence.validate_uart(raw,e,60)
        for events in ([],[dict(e[0],hex='00')],[dict(e[0],elapsed_ms=-1)],[dict(e[0],serial_error=8)],[dict(e[0],utc='2026-11-22T01:00:00')]):
            with self.assertRaises(ValueError):hardware_evidence.validate_uart(b'IRQ PASS\r\n',events,60)
    def test_missing_session_never_passes(self):
        with mock.patch.object(hardware,'context',return_value=(None,{})),self.assertRaises(FileNotFoundError):
            hardware_evidence.validate('build/T032/does-not-exist-session.json')
    def test_session_requires_two_ordered_captures_and_owner_observations(self):
        base=harness.inside('build/T032/policy-tests');base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as tmp,mock.patch.object(harness,'ROOT',Path(tmp)),mock.patch.object(hardware,'context',return_value=(None,{})):
            root=Path(tmp);(root/'evidence/hardware').mkdir(parents=True)
            records={'inventory':self.inv,'program':{'inventory':'inventory','target':self.target,'device':'xc7a35t_0','com':'COM3',
                'source_sha256':{},'bitstream_sha256':hardware.IMAGE_SHA,'targets':self.inv['targets'],'devices':self.inv['devices'],
                'commands':[{'status':'PASS','exit_code':0,'stdout':'HARDWARE_PROGRAM_PASS\n','stderr':''}],
                'finished_utc':'2026-11-22T01:00:00+00:00'}}
            for epoch in (1,2):
                name='capture'+str(epoch);folder=root/name;folder.mkdir()
                (folder/'uart.bin').write_bytes(b'IRQ PASS\r\n')
                (folder/'events.jsonl').write_text('{"elapsed_ms":5,"utc":"2026-11-22T01:0'+str(epoch)+':01+00:00","hex":"49525120504153530d0a"}\n',encoding='utf-8')
                (folder/'capture.json').write_text('{"seconds":5}',encoding='utf-8')
                records[name]={'program':'program','epoch':epoch,'com':'COM3','source_sha256':{},'output':name,
                    'commands':[{'status':'PASS','exit_code':0,'stdout':'HARDWARE_UART_CAPTURE_COMPLETE\n','stderr':''}],
                    'started_utc':'2026-11-22T01:0'+str(epoch)+':00+00:00','finished_utc':'2026-11-22T01:0'+str(epoch)+':06+00:00'}
            observations={'board':'Digilent Basys 3','done_led':True,'reset_epochs':[1,2],
                'owner_reply':'TEST FIXTURE, NOT PHYSICAL','question_item_id':'FIXTURE'}
            def save_obs():
                import json
                (root/'observations').write_text(json.dumps(observations),encoding='utf-8')
            save_obs()
            # Input bindings need real files; no fixtures enter evidence in real root.
            for n in ('program','capture1','capture2'):(root/n if n=='program' else root/n/'receipt').write_bytes(b'fixture')
            session={'schema_version':1,'kind':'physical_basys3','program':'program','captures':['capture1','capture2'],
                'observations':'observations','inputs_sha256':{'program':hardware.sha(root/'program'),'observations':hardware.sha(root/'observations')}}
            # Receipt names here are virtual; put hash-bound copies at root paths.
            session['captures']=['c1','c2'];records['c1']=records['capture1'];records['c2']=records['capture2']
            for n in ('c1','c2'):(root/n).write_bytes(b'fixture');session['inputs_sha256'][n]=hardware.sha(root/n)
            import json
            def verify():
                (root/'evidence/hardware/session.json').write_text(json.dumps(session),encoding='utf-8')
                with mock.patch.object(hardware,'bound_receipt',side_effect=lambda n,mode:records[n]):return hardware_evidence.validate()
            self.assertEqual(verify()['status'],'PASS')
            session['captures']=['c1','c1']
            with self.assertRaises(ValueError):verify()
            session['captures']=['c1','c2'];observations['done_led']=False;save_obs();session['inputs_sha256']['observations']=hardware.sha(root/'observations')
            with self.assertRaises(ValueError):verify()
            observations['done_led']=True;save_obs();session['inputs_sha256']['observations']=hardware.sha(root/'observations')
            records['c2']['epoch']=1
            with self.assertRaises(ValueError):verify()
    def test_live_authority_is_required_before_io(self):
        for state in ({'active':None,'task_states':{'T032':'pending'}},
                      {'active':'T032','task_states':{'T032':'in_progress','T043':'completed'},'start_approvals':{}}):
            with mock.patch.object(harness,'load',return_value=({},state)),self.assertRaises(ValueError):hardware.context()
    def test_saved_receipts_reject_missing_wrong_or_changed_artifacts(self):
        base=harness.inside('build/T032/policy-tests');base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as tmp,mock.patch.object(harness,'ROOT',Path(tmp)):
            root=Path(tmp);(root/'evidence/hardware').mkdir(parents=True)
            (root/'source').write_bytes(b'original source');(root/'artifact').write_bytes(b'original output')
            r={'status':'PASS','mode':'inventory','source_sha256':{'source':hardware.sha(root/'source')},'artifacts':{'artifact':hardware.sha(root/'artifact')}}
            import json
            (root/'evidence/hardware/proof.json').write_text(json.dumps(r),encoding='utf-8')
            hardware.bound_receipt('evidence/hardware/proof.json','inventory')
            (root/'artifact').write_bytes(b'changed output')
            with self.assertRaises(ValueError):hardware.bound_receipt('evidence/hardware/proof.json','inventory')
            with self.assertRaises(ValueError):hardware.bound_receipt('evidence/hardware/proof.json','program')
    def test_tcl_guard_and_part_selection_precede_programming(self):
        # Real Tcl interpreter, mocked hardware commands. No hardware or subprocess.
        base=harness.inside('build/T032/policy-tests');base.mkdir(parents=True,exist_ok=True)
        for case in ('inventory','good','wrong_target','wrong_part','guard_error','unknown_mode'):
            with self.subTest(case=case),tempfile.TemporaryDirectory(dir=base) as tmp:
                folder=Path(tmp);job=folder/'job.tsv';mode='inventory' if case=='inventory' else 'bad' if case=='unknown_mode' else 'program'
                target='other' if case=='wrong_target' else self.target
                job.write_text('mode\t'+mode+'\noutput\t'+str(folder)+'\npython\tfixture\ntarget\t'+('' if case=='inventory' else target)+'\ndevice\t'+('' if case=='inventory' else 'xc7a35t_0')+'\n',encoding='utf-8')
                t=tkinter.Tcl();calls=[]
                for name in ('open_hw_manager','connect_hw_server','current_hw_target','open_hw_target','set_property','close_hw_target','disconnect_hw_server','close_hw_manager'):
                    t.createcommand(name,lambda *args: '')
                t.createcommand('version',lambda *args:'2025.2')
                t.createcommand('get_hw_targets',lambda:self.target)
                t.createcommand('get_hw_devices',lambda:'xc7a35t_0')
                t.createcommand('get_property',lambda *args:'xc7a100t' if case=='wrong_part' else 'xc7a35t')
                t.createcommand('list_property',lambda *args:'PART')
                t.createcommand('program_hw_devices',lambda *args:calls.append('program') or '')
                t.eval('rename exec real_exec; proc exec {args} {return HARDWARE_GUARD_PASS}')
                if case=='guard_error':t.eval('proc exec {args} {error GUARD_REJECTED}')
                t.setvar('argc',1);t.setvar('argv',t.call('list',str(job)))
                if case in ('inventory','good'):t.call('source',str(harness.inside('scripts/hardware.tcl')))
                else:
                    with self.assertRaises(tkinter.TclError):t.call('source',str(harness.inside('scripts/hardware.tcl')))
                self.assertEqual(calls,['program'] if case=='good' else [])


if __name__=='__main__':unittest.main()
