import hashlib
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest
from mat3ra.utils import file as utils
from mat3ra.utils.file import file_sha256, write_file

REFERENCE_FILE_PATH = Path(__file__).parent / "./fixtures/file_with_content.txt"
REFERENCE_FILE_CONTENT = """Content Line 1\nContent Line 2\nContent Line 3\n"""


def test_file_get_content():
    content = utils.get_file_content(REFERENCE_FILE_PATH)
    assert content == REFERENCE_FILE_CONTENT


def test_file_append_line():
    line = "Content Line 4"
    reference_file_copy_path = REFERENCE_FILE_PATH.with_name("file_with_content_test_file_append_line.txt")
    shutil.copy(REFERENCE_FILE_PATH, reference_file_copy_path)
    utils.append_line_to_file(line, reference_file_copy_path)
    content = utils.get_file_content(reference_file_copy_path)
    assert line in content
    Path.unlink(reference_file_copy_path)


def test_file_remove_line():
    pattern = "Content Line 2"
    reference_file_copy_path = REFERENCE_FILE_PATH.with_name("file_with_content_test_file_remove_line.txt")
    shutil.copy(REFERENCE_FILE_PATH, reference_file_copy_path)
    utils.remove_line_containing_pattern(pattern, reference_file_copy_path)
    content = utils.get_file_content(reference_file_copy_path)
    assert pattern not in content
    Path.unlink(reference_file_copy_path)


def test_file_get_tmp_logfile_basename():
    log_basename = utils.get_tmp_logfile_basename()
    assert log_basename.startswith("tmp-")
    assert log_basename.endswith(".log")


def test_file_replacement_preservation_and_byte_hash(tmp_path, monkeypatch):
    path = tmp_path / "output.txt"
    write_file(path, "original")
    write_file(path, "Plain text: \u03b1\n")
    original = path.read_bytes()
    assert original == "Plain text: \u03b1\n".encode("utf-8")
    assert file_sha256(path) == hashlib.sha256(original).hexdigest()
    monkeypatch.setattr(Path, "replace", Mock(side_effect=OSError("replacement failed")))
    with pytest.raises(OSError, match="replacement failed"):
        write_file(path, "replacement")
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]
