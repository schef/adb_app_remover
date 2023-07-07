#!/usr/bin/env python

import os
import sys
import shutil
import select
import pty
from subprocess import Popen

ADB_LIST="adb shell pm list packages -3 | cut -d: -f2"
ADB_REMOVE_PRE="adb uninstall"

def run_bash_cmd(cmd, echo=False, interaction={}, return_lines=True, return_code=False, cr_as_newline=False):
    if echo: print("CMD:", cmd)
    master_fd, slave_fd = pty.openpty()
    line = ""
    lines = []
    with Popen(cmd, shell=True, preexec_fn=os.setsid, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, universal_newlines=True) as p:
        while p.poll() is None:
            r, w, e = select.select([sys.stdin, master_fd], [], [], 0.01)
            if master_fd in r:
                o = os.read(master_fd, 10240).decode("UTF-8")
                if o:
                    for c in o:
                        if cr_as_newline and c == "\r":
                            c = "\n"
                        if c == "\n":
                            if line and line not in interaction.values():
                                clean = line.strip().split('\r')[-1]
                                lines.append(clean)
                                if echo: print("STD:", line)
                            line = ""
                        else:
                            line += c
            if line:  # pass password to prompt
                for key in interaction:
                    if key in line:
                        if echo: print("PMT:", line)
                        sleep(1)
                        os.write(master_fd, ("%s" % (interaction[key])).encode())
                        os.write(master_fd, "\r\n".encode())
                        line = ""
        if line:
            clean = line.strip().split('\r')[-1]
            lines.append(clean)

    os.close(master_fd)
    os.close(slave_fd)

    if return_lines and return_code:
        return lines, p.returncode
    elif return_code:
        return p.returncode
    else:
        return lines

ignore_packages = ["com.google.android.apps.youtube.kids",
        "com.google.android.apps.kids.familylink",
        "com.google.android.youtube",
        "com.google.android.apps.youtube.music",
        ]

if __name__ == "__main__":
    adb_packages = run_bash_cmd(ADB_LIST)
    for package in adb_packages:
        if package not in ignore_packages:
            cmd = "%s %s" % (ADB_REMOVE_PRE, package)
            print("removing %s" % (package))
            run_bash_cmd(cmd)
