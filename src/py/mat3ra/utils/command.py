import os
import shlex
import signal
import subprocess
import time
from contextlib import contextmanager
from functools import partial
from threading import Timer
from types import FrameType
from typing import Dict, Iterator, List, Optional

TIMEOUT_RETURNCODE = -1000


def run_command_with_log(arguments: list, log_path, timeout: float, **options) -> None:
    """
    Run a POSIX process group with a live log; kill all children on timeout or interruption.

    Unlike the captured-output helpers, output is streamed to disk. Popen's cwd
    and env can be supplied through options. Failures raise CalledProcessError;
    timeouts retain partial output and raise TimeoutExpired after cleanup.
    """
    with open(log_path, "w") as output:
        process = subprocess.Popen(
            arguments, stdout=output, stderr=subprocess.STDOUT, start_new_session=True, **options
        )
        try:
            returncode = process.wait(timeout=timeout)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
    if returncode:
        raise subprocess.CalledProcessError(returncode, arguments)


def run_command_with_timeout(args: list, timeout: int = 30, **kwargs):
    """
    Execute a shell command and return exit code, stdout and stderr. The command is executed through Popen and it
    will be killed after `timeout` seconds.

    Args:
        args (list): A list containing command name and its arguments.
        timeout (int): timeout in second. Defaults to 30.

    Returns:
            tuple: (returncode, stdout, stderr)
    """
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
    t = Timer(timeout, p.terminate)
    t.start()
    stdout, stderr = p.communicate()
    returncode, stdout, stderr = p.returncode, stdout, stderr
    if t.is_alive():
        t.cancel()
    else:
        returncode, stdout, stderr = TIMEOUT_RETURNCODE, "", "ERROR: command timed out."
    return returncode, stdout, stderr


def run_command(command: str, timeout: int = 30, **kwargs):
    """
    Execute a shell command and return exit code, stdout and stderr. The command is executed through Popen and it
    will be killed after `timeout` seconds.

    Args:
        command (str): command to execute.
        timeout (int): timeout in second. Defaults to 30.

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    retcode, stdout, stderr = run_command_with_timeout(shlex.split(command), timeout, **kwargs)
    if retcode != 0:
        print(f"run_command failed, retcode={retcode} stdout={stdout}, stderr={stderr}")
        raise RuntimeError
    return retcode, stdout, stderr


@contextmanager
def execution_deadline(seconds: float, grace_seconds: float = 5.0) -> Iterator[None]:
    """
    Give the block `seconds` and stop what it left behind if that was not enough.

    For a call made in this process that starts processes it does not hand back, such as
    a runner that launches a simulation and waits for it: `run_command_with_log` can
    put a timeout on a process it starts, but not on a call that starts its own.
    `TimeoutError` is raised inside the block once `seconds` have passed, through
    `SIGALRM`, so this is POSIX-only, may only be used from the main thread, and only
    one deadline can be in effect at a time.

    A call interrupted that way does not get to finish its own cleanup, so when the
    deadline is what ended the block every process descended from this one is stopped
    (see `stop_descendant_processes`). That happens only after a deadline: on an
    ordinary return the descendants of this process are left alone.

    Whether the deadline is what ended the block is read off the timer: a one-shot
    interval timer reports no time remaining once it has fired, and time remaining
    while it is still pending.
    """
    previous_handler = signal.signal(signal.SIGALRM, partial(raise_the_time_limit, seconds=seconds))
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        expired = signal.getitimer(signal.ITIMER_REAL)[0] == 0.0
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if expired:
            stop_descendant_processes(grace_seconds)


def raise_the_time_limit(number: int, frame: Optional[FrameType], seconds: float) -> None:
    """
    The `SIGALRM` handler `execution_deadline` installs; raises where the running call is.
    """
    raise TimeoutError(f"the {seconds:g} second time limit passed")


def stop_descendant_processes(grace_seconds: float = 5.0) -> List[int]:
    """
    Signal every process descended from this one and return the ones signalled.

    `SIGTERM` first, then `SIGKILL` to whatever is still there `grace_seconds` later.
    Children started without `start_new_session` share this process group with whatever
    started this process, so the group cannot be signalled as a whole; the tree is
    walked from this process instead and each process below it signalled on its own.
    """
    descendants = descendant_process_identifiers()
    for signal_number in (signal.SIGTERM, signal.SIGKILL):
        remaining = []
        for process_identifier in descendants:
            try:
                os.kill(process_identifier, signal_number)
            except OSError:
                continue
            remaining.append(process_identifier)
        if not remaining or signal_number is signal.SIGKILL:
            break
        time.sleep(grace_seconds)
        descendants = remaining
    return descendants


def descendant_process_identifiers() -> List[int]:
    """
    Every process below this one, deepest first, as `ps` reports the parentage.

    Deepest first so a child is signalled before the process that would notice it died
    and start another.
    """
    listing = subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True, check=False)
    children: Dict[int, List[int]] = {}
    for line in listing.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2 and all(field.isdigit() for field in fields):
            process_identifier, parent = (int(field) for field in fields)
            children.setdefault(parent, []).append(process_identifier)
    generation = children.get(os.getpid(), [])
    descendants: List[int] = []
    while generation:
        descendants = generation + descendants
        generation = [
            child
            for process_identifier in generation
            for child in children.get(process_identifier, [])
            if child not in descendants
        ]
    return descendants
