"""Volume initialization must drop privileges before starting the web server."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch


ROOT = Path(__file__).resolve().parents[1]
if os.name == "nt":
    raise unittest.SkipTest("Container privilege tests require a Unix host")
spec = importlib.util.spec_from_file_location("jisr_entrypoint", ROOT / "docker-entrypoint.py")
entrypoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entrypoint)


class ContainerStartupTests(unittest.TestCase):
    def test_new_disk_ownership_and_privileges_before_exec(self):
        with tempfile.TemporaryDirectory() as folder:
            user = SimpleNamespace(pw_uid=10001, pw_gid=10001)
            order = Mock()
            with patch.dict(entrypoint.os.environ, {"JISR_DATA_DIR": folder}), \
                    patch.object(entrypoint.os, "geteuid", return_value=0), \
                    patch.object(entrypoint.pwd, "getpwnam", return_value=user), \
                    patch.object(entrypoint.os, "chown") as chown, \
                    patch.object(entrypoint.os, "setgroups") as groups, \
                    patch.object(entrypoint.os, "setgid") as gid, \
                    patch.object(entrypoint.os, "setuid") as uid, \
                    patch.object(entrypoint.os, "access", return_value=True), \
                    patch.object(entrypoint.os, "execvp") as execute, \
                    patch.object(entrypoint.sys, "argv", ["docker-entrypoint.py", "python", "server.py"]):
                for name, mock in (("chown", chown), ("groups", groups), ("gid", gid), ("uid", uid), ("execute", execute)):
                    order.attach_mock(mock, name)
                entrypoint.main()
                self.assertEqual(order.mock_calls, [
                    call.chown(Path(folder).resolve(), 10001, 10001), call.groups([]),
                    call.gid(10001), call.uid(10001), call.execute("python", ["python", "server.py"]),
                ])

    def test_unwritable_disk_never_starts_server(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(entrypoint.os.environ, {"JISR_DATA_DIR": folder}), \
                    patch.object(entrypoint.os, "geteuid", return_value=10001), \
                    patch.object(entrypoint.pwd, "getpwnam") as lookup, \
                    patch.object(entrypoint.os, "access", return_value=False), \
                    patch.object(entrypoint.os, "execvp") as execute:
                with self.assertRaisesRegex(SystemExit, "writable"):
                    entrypoint.main()
                lookup.assert_not_called()
                execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
