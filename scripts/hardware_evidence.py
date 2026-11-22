"""Validate recorded physical observations; never connect/program hardware."""
import datetime as dt
import json
import sys
from pathlib import Path
import hardware as hw
import harness


def validate_uart(raw,events,seconds):
    if raw != b'IRQ PASS\r\n':raise ValueError('HARDWARE_UART_EXACT_BYTES')
    data=bytearray();previous=-1.0
    if not events:raise ValueError('HARDWARE_UART_MISSING_EVENTS')
    for event in events:
        if 'serial_error' in event:raise ValueError('HARDWARE_UART_ERROR')
        elapsed=event['elapsed_ms']
        if not isinstance(elapsed,(int,float)) or not 0<=elapsed or not previous<=elapsed<=(seconds+1)*1000:
            raise ValueError('HARDWARE_UART_EVENT_TIME')
        previous=elapsed
        stamp=dt.datetime.fromisoformat(event['utc'])
        if stamp.tzinfo is None:raise ValueError('HARDWARE_UART_EVENT_TIMEZONE')
        data.extend(bytes.fromhex(event['hex']))
    if bytes(data)!=raw:raise ValueError('HARDWARE_UART_EVENT_RAW_MISMATCH')


def validate(name='evidence/hardware/session.json'):
    _,sources=hw.context()
    path=harness.inside(name)
    if not path.is_file():raise FileNotFoundError('No completed physical hardware session')
    session=harness.read(path)
    if session['schema_version']!=1 or session['kind']!='physical_basys3':raise ValueError('HARDWARE_SESSION_SCHEMA')
    for n,d in session['inputs_sha256'].items():
        if hw.sha(harness.inside(n))!=d:raise ValueError('HARDWARE_SESSION_INPUT_DRIFT '+n)
    program=hw.bound_receipt(session['program'],'program')
    inv=hw.bound_receipt(program['inventory'],'inventory')
    hw.select_device(inv,program['target'],program['device'],program['com'])
    if program['source_sha256']!=sources or program['bitstream_sha256']!=hw.IMAGE_SHA:
        raise ValueError('HARDWARE_PROGRAM_INPUT_DRIFT')
    if len(program['commands'])!=1 or not hw.native_ok(program['commands'][0],'HARDWARE_PROGRAM_PASS'):
        raise ValueError('HARDWARE_PROGRAM_COMMAND')
    if program['targets']!=inv['targets'] or program['devices']!=inv['devices']:
        raise ValueError('HARDWARE_PROGRAM_DEVICE_CHANGED')
    captures=session['captures']
    if len(captures)!=2 or len(set(captures))!=2:raise ValueError('HARDWARE_TWO_RESET_EPOCHS')
    previous=dt.datetime.fromisoformat(program['finished_utc'])
    for epoch,n in enumerate(captures,1):
        c=hw.bound_receipt(n,'capture')
        if c['program']!=session['program'] or c['epoch']!=epoch or c['com']!=program['com'] or c['source_sha256']!=sources:
            raise ValueError('HARDWARE_CAPTURE_EPOCH_BINDING')
        if len(c['commands'])!=1 or not hw.native_ok(c['commands'][0],'HARDWARE_UART_CAPTURE_COMPLETE'):
            raise ValueError('HARDWARE_CAPTURE_COMMAND')
        if dt.datetime.fromisoformat(c['started_utc'])<previous:raise ValueError('HARDWARE_EPOCH_TIME_ORDER')
        previous=dt.datetime.fromisoformat(c['finished_utc'])
        folder=harness.inside(c['output']);job=harness.read(folder/'capture.json')
        events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        validate_uart((folder/'uart.bin').read_bytes(),events,job['seconds'])
        if n not in session['inputs_sha256']:raise ValueError('HARDWARE_UNBOUND_CAPTURE')
    observations=harness.read(harness.inside(session['observations']))
    if (observations.get('board')!='Digilent Basys 3' or observations.get('done_led') is not True or
            observations.get('reset_epochs')!=[1,2] or not observations.get('owner_reply') or not observations.get('question_item_id')):
        raise ValueError('HARDWARE_OWNER_OBSERVATION_REQUIRED')
    if session['program'] not in session['inputs_sha256'] or session['observations'] not in session['inputs_sha256']:
        raise ValueError('HARDWARE_UNBOUND_SESSION_INPUT')
    return {'status':'PASS','scope':'Physical Basys3 approved image, two warm-reset IRQ PASS UART observations only',
        'program':session['program'],'captures':captures,'bitstream_sha256':hw.IMAGE_SHA,
        'formal':'T023 skipped / NOT RUN','asic':'NOT RUN'}


def main():
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path=harness.inside('evidence/hardware/check-'+stamp+'.json')
    try:result=validate();code=0
    except FileNotFoundError as exc:result={'status':'NOT RUN','error':str(exc)};code=125
    except (ValueError,KeyError,OSError,harness.Stop) as exc:result={'status':'FAIL','error':str(exc)};code=1
    result['date_la']=harness.today();harness.atomic(path,result)
    print(json.dumps(dict(result,receipt=hw.rel(path))));return code


if __name__=='__main__':sys.exit(main())
