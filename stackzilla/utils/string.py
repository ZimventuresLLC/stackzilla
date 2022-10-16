"""String utilities."""

def removeprefix(string: str, prefix: str) -> str:
    """Remove the prefix of a string.

        str.removeprefix() is not available in prior to Python 3.9
    Args:
        string (str): The string to work on
        prefix (str): The prefix to remove from string

    Returns:
        str: A string with the prefix removed (if present)
    """
    if string.startswith(prefix):
        return string[len(prefix):]

    return string
