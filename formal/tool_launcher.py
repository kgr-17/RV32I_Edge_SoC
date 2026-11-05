#!/usr/bin/env python3
"""Use installed tool directories only in this child process, never host PATH."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    commands=json.loads(sys.argv[1]);argv=json.loads(sys.argv[2]);folders=[]
    for command in commands.values():
        for token in command:
            path=Path(token)
            if path.is_absolute() and path.is_file():
                folder=str(path.parent)
                if folder not in folders:folders.append(folder)
    env=dict(os.environ)
    env['PATH']=os.pathsep.join(folders+[env.get('PATH','')])
    return subprocess.call(argv,env=env,shell=False)


if __name__=='__main__':sys.exit(main())
