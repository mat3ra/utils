import subprocess
import sys
import time

import pytest
from mat3ra.utils import command as utils
from mat3ra.utils.command import TIMEOUT_RETURNCODE, run_command_with_log

COMMAND_TO_SUCCEED = "echo 'Hello, World!'"
COMMAND_TO_FAIL = "false"
COMMAND_TO_TIMEOUT = "sleep 10"


def test_run_command_to_succeed():
    retcode, stdout, stderr = utils.run_command(COMMAND_TO_SUCCEED)
    assert retcode == 0
    assert stdout == "Hello, World!\n"
    assert stderr == ""


def test_run_command_failure(monkeypatch):
    # Define a mock function to replace subprocess.Popen
    class MockPopen:
        def __init__(self, *args, **kwargs):
            self._terminated = None
            self.returncode = 1  # Simulate a failure
            self.args = args

        def communicate(self):
            return "", "error message"  # Simulate empty stdout and error in stderr

        def terminate(self):
            self._terminated = True  # Flag to indicate terminate was called
            self.returncode = -1  # Simulate timeout behavior with a returncode

    # Use monkeypatch to replace subprocess.Popen with MockPopen
    monkeypatch.setattr(subprocess, "Popen", MockPopen)

    # Run the test, expecting a RuntimeError due to command failure
    with pytest.raises(RuntimeError):
        utils.run_command(COMMAND_TO_FAIL)


def test_run_command_to_timeout():
    with pytest.raises(RuntimeError):
        retcode, stdout, stderr = utils.run_command(COMMAND_TO_TIMEOUT, timeout=1)
        assert retcode == TIMEOUT_RETURNCODE
        assert stdout == ""
        assert stderr == "ERROR: command timed out."


def test_logged_command_keeps_output_on_failure(tmp_path):
    path = tmp_path / "execution.log"
    with pytest.raises(subprocess.CalledProcessError):
        run_command_with_log([sys.executable, "-u", "-c", "print('partial evidence'); raise SystemExit(3)"], path, 5)
    assert "partial evidence" in path.read_text()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups")
def test_timeout_stops_child_process_and_preserves_live_log(tmp_path):
    path = tmp_path / "execution.log"
    child = "import time; time.sleep(1); open('child-finished', 'w').write('unexpected')"
    parent = (
        "import subprocess, sys, time; "
        f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
        "print('child started', flush=True); time.sleep(30)"
    )
    with pytest.raises(subprocess.TimeoutExpired):
        run_command_with_log([sys.executable, "-u", "-c", parent], path, 0.5, cwd=tmp_path)
    assert "child started" in path.read_text()
    time.sleep(1)
    assert not (tmp_path / "child-finished").exists()
