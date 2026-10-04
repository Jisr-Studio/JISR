"""Make a new persistent disk writable, then drop root before starting Jisr."""

import os
import pwd
import sys
from pathlib import Path


def main():
    data = Path(os.environ.get("JISR_DATA_DIR", "/app/data")).resolve()
    data.mkdir(parents=True, exist_ok=True)
    if os.geteuid() == 0:
        user = pwd.getpwnam("jisr")
        # Existing project files already belong to this stable UID. Only the
        # mount root needs ownership when a cloud platform attaches a new disk.
        os.chown(data, user.pw_uid, user.pw_gid)
        os.setgroups([])
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)
    if not os.access(data, os.W_OK):
        raise SystemExit("JISR_DATA_DIR must be writable by the application user")
    args = sys.argv[1:] or [sys.executable, "server.py"]
    os.execvp(args[0], args)


if __name__ == "__main__":
    main()
