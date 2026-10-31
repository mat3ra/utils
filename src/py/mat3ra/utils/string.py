import hashlib
import hmac
import re


def sha1_hash(string: str) -> str:
    """Returns SHA1 hash of a string."""
    h = hashlib.sha1()
    h.update(string.encode())
    return h.hexdigest()


def compute_digest(message, hash_function: str = "md5", hex_digest: bool = False):
    """
    Computes message digest for data integrity.

    Args:
        message (str): message passed to hash function.
        hash_function (str): hash function name.
        hex_digest (bool): whether to return hex digest.

    Returns:
        bytes: The digest of the message.
    """
    h = getattr(hashlib, hash_function)()
    h.update(message.encode())
    return h.hexdigest() if hex_digest else h.digest()


def compute_signature(message: str, key: str, hash_function: str = "md5"):
    """
    Computes signature for data origin authentication.
        It uses HMAC algorithm.

    Args:
        message (bytes): message passed to the HMAC.
        key (str): key used for HMAC.
        hash_function (str): hash function name.

    Returns:
        bytes: The digest of the message.
    """
    return hmac.new(key.encode(), message, digestmod=hash_function).digest()  # type: ignore


def camel_to_snake(camel_case_str: str) -> str:
    """
    Convert CamelCase string to snake_case.
    """
    words = re.findall(r"[A-Z][a-z]*", camel_case_str)
    return "_".join(words).lower()


def snake_to_camel(snake_case_str: str) -> str:
    """
    Convert snake_case string to CamelCase.
    """
    parts = snake_case_str.split("_")
    return "".join(x.title() for x in parts)


def remove_comments_from_source_code(text: str, language: str = "shell") -> str:
    """
    Removes comments from source code based on the language.
    TODO: consider preserving values enclosed in quotes. support for following cases:
        url="https://www.example.com/about#company"
        message = "Hello, world!"
        var = 2  # it's a comment
    """
    patterns = {
        "fortran": r"!.*$",  # ! comments only
        "python": r"#.*$",
        "shell": r"#(?!!).*$",  # # comments (except shebang)
    }
    return re.sub(patterns.get(language, patterns["shell"]), "", text, flags=re.MULTILINE)


def remove_empty_lines_from_string(text: str) -> str:
    """Removes empty lines and trims."""
    return re.sub(r"^\s*[\r\n]", "", text, flags=re.MULTILINE).strip()
