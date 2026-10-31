import uuid


def get_uuid() -> str:
    """
    Generates a UUID v4 string.

    Returns:
        str: A UUID string.
    """
    return str(uuid.uuid4())


def get_uuid_from_namespace(seed: str = "", namespace: str = "00000000-0000-4000-8000-000000000000") -> str:
    """
    Generates a UUID v5 string based on a namespace and seed.

    Args:
        seed (str, optional): The seed string. Defaults to "".
        namespace (str, optional): The namespace UUID string. Defaults to "00000000-0000-4000-8000-000000000000".

    Returns:
        str: A UUID string.
    """
    namespace_uuid = uuid.UUID(namespace)
    return str(uuid.uuid5(namespace_uuid, seed))
