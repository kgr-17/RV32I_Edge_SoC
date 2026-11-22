"""Read-only bounded Windows UART capture through Win32, without dependencies."""
import ctypes
from ctypes import wintypes as w
import datetime as dt
import json
import time


class DCB(ctypes.Structure):
    _fields_=[('length',w.DWORD),('baud',w.DWORD),('flags',w.DWORD),('reserved',w.WORD),
        ('xon_limit',w.WORD),('xoff_limit',w.WORD),('byte_size',w.BYTE),('parity',w.BYTE),
        ('stop_bits',w.BYTE),('xon',ctypes.c_char),('xoff',ctypes.c_char),('error',ctypes.c_char),
        ('eof',ctypes.c_char),('event',ctypes.c_char),('reserved1',w.WORD)]


class Timeouts(ctypes.Structure):
    _fields_=[(name,w.DWORD) for name in ('interval','read_multiplier','read_constant','write_multiplier','write_constant')]


def capture(com,seconds,folder):
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
    api.CreateFileW.restype=w.HANDLE
    for name,args in [('GetCommState',[w.HANDLE,ctypes.POINTER(DCB)]),('SetCommState',[w.HANDLE,ctypes.POINTER(DCB)]),
            ('SetCommTimeouts',[w.HANDLE,ctypes.POINTER(Timeouts)]),('ClearCommError',[w.HANDLE,ctypes.POINTER(w.DWORD),ctypes.c_void_p]),
            ('ReadFile',[w.HANDLE,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD),ctypes.c_void_p]),('CloseHandle',[w.HANDLE])]:
        getattr(api,name).argtypes=args;getattr(api,name).restype=w.BOOL
    handle=api.CreateFileW('\\\\.\\'+com,0x80000000,0,None,3,0,None)
    if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    def checked(value):
        if not value:raise ctypes.WinError(ctypes.get_last_error())
    try:
        dcb=DCB();dcb.length=ctypes.sizeof(DCB);checked(api.GetCommState(handle,ctypes.byref(dcb)))
        dcb.baud=115200;dcb.flags=1;dcb.byte_size=8;dcb.parity=0;dcb.stop_bits=0
        checked(api.SetCommState(handle,ctypes.byref(dcb)))
        timeout=Timeouts(0xffffffff,0,100,0,100);checked(api.SetCommTimeouts(handle,ctypes.byref(timeout)))
        with (folder/'uart.bin').open('xb') as raw,(folder/'events.jsonl').open('x',encoding='utf-8') as events:
            start=time.monotonic();buf=ctypes.create_string_buffer(256)
            print('HARDWARE_UART_READY '+com,flush=True)
            while time.monotonic()-start<seconds:
                errors=w.DWORD();checked(api.ClearCommError(handle,ctypes.byref(errors),None))
                if errors.value:
                    events.write(json.dumps({'serial_error':errors.value,'utc':dt.datetime.now(dt.timezone.utc).isoformat()})+'\n');events.flush()
                    raise OSError('HARDWARE_UART_SERIAL_ERROR '+str(errors.value))
                count=w.DWORD();checked(api.ReadFile(handle,buf,len(buf),ctypes.byref(count),None))
                if count.value:
                    data=buf.raw[:count.value];raw.write(data);raw.flush()
                    events.write(json.dumps({'elapsed_ms':(time.monotonic()-start)*1000,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'hex':data.hex()})+'\n');events.flush()
            print('HARDWARE_UART_CAPTURE_COMPLETE',flush=True)
    finally:api.CloseHandle(handle)
