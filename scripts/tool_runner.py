#!/usr/bin/env python3
"""Project-local command evidence and process-tree timeout cleanup; not a sandbox."""
import ctypes
from ctypes import wintypes
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import tempfile
import harness


class WindowsJob:
    def __init__(self):
        class Basic(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                        ('flags', wintypes.DWORD), ('min_ws', ctypes.c_size_t),
                        ('max_ws', ctypes.c_size_t), ('active', wintypes.DWORD),
                        ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD),
                        ('scheduling', wintypes.DWORD)]

        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in
                        ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]

        class Extended(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', IO), ('process_mem', ctypes.c_size_t),
                        ('job_mem', ctypes.c_size_t), ('peak_process', ctypes.c_size_t),
                        ('peak_job', ctypes.c_size_t)]

        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.api.SetInformationJobObject.restype = wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def attach(self, process):
        if not self.api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(process._handle))):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def run(argv, cwd, timeout=30):
    """Return full command output; release child only after tree cleanup is armed."""
    cwd = Path(cwd).resolve()
    if not cwd.is_relative_to(harness.ROOT.resolve()):
        raise harness.Stop('Tool cwd must stay in project')
    if not argv or not all(isinstance(arg, str) and arg for arg in argv):
        raise ValueError('Expected nonempty exact argv')
    if not 0 < timeout <= 120:
        raise ValueError('Tool timeout must be between zero and 120 seconds')
    cwd.mkdir(parents=True, exist_ok=True)
    env = harness.local_env()
    # Native SDK launchers may use fixed temporary basenames. Keep each command
    # in a compact, unique project-local directory, including parallel runs.
    temporary_base=harness.inside('build/tmp')
    temporary_base.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='eda-',dir=str(temporary_base)))
    for name in ('TMP','TEMP','TMPDIR'):env[name]=str(temporary)
    for name in ('APPDATA', 'LOCALAPPDATA', 'USERPROFILE'):
        folder = cwd / 'profile' / name.lower()
        folder.mkdir(parents=True, exist_ok=True)
        env[name] = str(folder)
    record = {'argv': argv, 'cwd': str(cwd), 'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'timeout_seconds': timeout, 'exit_code': None, 'status': 'NOT RUN',
              'stdout': '', 'stderr': '', 'temporary_directory':str(temporary),
              'cleanup': 'Windows Job Object' if os.name == 'nt' else 'POSIX process group'}
    started = time.monotonic()
    job = None
    process = None
    try:
        job = WindowsJob() if os.name == 'nt' else None
        options = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
        process = subprocess.Popen(
            [sys.executable, '-B', str(harness.inside('scripts/tool_child.py')), json.dumps(argv)],
            cwd=str(cwd), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', **options)
        if job:
            job.attach(process)
        try:
            stdout, stderr = process.communicate(input='GO\n', timeout=timeout)
            record.update(exit_code=process.returncode, stdout=stdout, stderr=stderr,
                          status='PASS' if process.returncode == 0 else 'NOT RUN' if process.returncode in (125, 127) else 'FAIL')
        except subprocess.TimeoutExpired:
            if job:
                job.close()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate(timeout=10)
            record.update(exit_code=process.returncode, stdout=stdout, stderr=stderr, status='TIMEOUT')
    except OSError as exc:
        record['stderr'] = str(exc)
    finally:
        if job:
            job.close()
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate(timeout=10)
    record['duration_seconds'] = round(time.monotonic() - started, 3)
    return record


def vendor_argv(name, args):
    config = harness.read(harness.inside('.harness/toolchain.json'))
    path = config.get('tools', {}).get(name)
    if not path or not Path(path).is_file():
        raise FileNotFoundError('Configured tool unavailable: ' + name)
    argv = [path] + list(args)
    if os.name == 'nt' and Path(path).suffix.lower() in ('.bat', '.cmd'):
        # Batch launchers require cmd. Limit this interface to fixed, shell-safe tokens.
        if any(any(char.isspace() or char in '&|<>^%!()"\r\n' for char in arg) for arg in argv):
            raise ValueError('Batch tool paths/arguments must contain no whitespace or cmd metacharacters')
        return ['cmd.exe', '/d', '/c'] + argv
    return argv
