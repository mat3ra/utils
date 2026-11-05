import os
import signal
import subprocess
import sys
import time

import pytest
from mat3ra.utils import command as utils
from mat3ra.utils.command import (
    TIMEOUT_RETURNCODE,
    descendant_process_identifiers,
    execution_deadline,
    run_command_with_log,
)

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


POSIX_ONLY = pytest.mark.skipif(sys.platform == "win32", reason="SIGALRM and ps")


def start_child_with_its_own_child():
    """
    A child holding a `sleep` of its own, as a runner holding a simulation would.
    """
    child = subprocess.Popen(["sh", "-c", "sleep 60 & echo $!; wait"], stdout=subprocess.PIPE, text=True)
    return child, int(child.stdout.readline())


def running(process_identifier):
    """
    Whether `ps` still reports that process.
    """
    return subprocess.run(["ps", "-p", str(process_identifier)], capture_output=True, check=False).returncode == 0


@POSIX_ONLY
def test_execution_deadline_interrupts_the_call_it_wraps():
    with pytest.raises(TimeoutError, match="0.05 second time limit passed"):
        with execution_deadline(0.05):
            time.sleep(60)


@POSIX_ONLY
def test_execution_deadline_restores_the_timer_and_the_previous_handler():
    def handler(number, frame):
        raise AssertionError("the previous handler must be restored, not called")

    previous = signal.signal(signal.SIGALRM, handler)
    try:
        with pytest.raises(TimeoutError):
            with execution_deadline(0.05):
                time.sleep(60)
        assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
        assert signal.getsignal(signal.SIGALRM) is handler
    finally:
        signal.signal(signal.SIGALRM, previous)


@POSIX_ONLY
def test_execution_deadline_leaves_the_children_of_a_call_that_returns_in_time():
    child, grandchild_identifier = start_child_with_its_own_child()
    try:
        with execution_deadline(60):
            value = "returned"
        assert value == "returned"
        assert child.poll() is None
        assert running(grandchild_identifier)
    finally:
        child.kill()
        child.wait()


@POSIX_ONLY
def test_execution_deadline_stops_the_processes_an_interrupted_call_left_behind():
    child, grandchild_identifier = start_child_with_its_own_child()
    try:
        with pytest.raises(TimeoutError):
            with execution_deadline(0.05, grace_seconds=0.2):
                time.sleep(60)
        assert child.wait(timeout=10) != 0
        deadline_to_disappear = time.monotonic() + 10
        while running(grandchild_identifier) and time.monotonic() < deadline_to_disappear:
            time.sleep(0.1)
        assert not running(grandchild_identifier)
    finally:
        child.kill()
        child.wait()


@POSIX_ONLY
def test_descendant_process_identifiers_lists_the_deepest_first():
    child, grandchild_identifier = start_child_with_its_own_child()
    try:
        descendants = descendant_process_identifiers()
        assert {child.pid, grandchild_identifier} <= set(descendants)
        assert descendants.index(grandchild_identifier) < descendants.index(child.pid)
        assert os.getpid() not in descendants
    finally:
        child.kill()
        child.wait()
