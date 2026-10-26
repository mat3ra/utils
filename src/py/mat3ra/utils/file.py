import fcntl
import hashlib
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile


def file_sha256(path) -> str:
    """Hash file bytes without loading large artifacts into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_file_content(path, content: str) -> None:
    """Write UTF-8 text to a temporary file, then replace the destination after the write succeeds."""
    path = Path(path)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(content)
            stream.close()
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()


def get_file_content(file_path: str) -> str:
    """
    Returns the content of a given file.

    Args:
        file_path (str): file path.

    Returns:
         str
    """
    content = ""
    if file_path and os.path.exists(file_path):
        with open(file_path) as f:
            content = f.read()
    return content


def append_line_to_file(line: str, file_path: str, add_newline: bool = True):
    """
    Append line to given file.

    Args:
        line (str): line to add. End of line (EOL) is added automatically.
        file_path (str): file path
    """
    with open(file_path, "a+") as f:
        f.write(line + "\n" if add_newline else "")


def remove_line_containing_pattern(pattern: str, file_path: str):
    """
    Removes line containing given pattern form the file.

    Args:
        pattern (str): pattern to look for.
        file_path (str): file path
    """
    with open(file_path, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        for line in lines:
            if pattern not in line:
                f.write(line)


# Logfile management
TMP_LOG_LATEST_BASENAME = "tmp-latest.log"
TMP_LOG_REGEX = "tmp-*.log"


def get_tmp_logfile_basename(use_timestamp=True):
    """
    Returns the basename of the log file for provision output.

    Args:
        use_timestamp (bool): whether to include timestamp in the log file name. Default is True.

    Returns:
        str: log file basename
    """
    timestamp = "latest"
    if use_timestamp:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
    return f"tmp-{timestamp}.log"
