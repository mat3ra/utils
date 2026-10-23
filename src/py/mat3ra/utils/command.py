import os
import shlex
import signal
import subprocess
from threading import Timer

TIMEOUT_RETURNCODE = -1000


def run_command_with_log(arguments: list, log_path, timeout: float, **options) -> None:
    """Run a POSIX process group with a live log; kill all children on timeout or interruption.

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
