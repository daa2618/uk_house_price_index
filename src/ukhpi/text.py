import re


def split_camel_case(s: str) -> list[str]:
    regex = (
        r"(?<=[a-z])(?=[A-Z])|"
        r"(?<=[A-Z])(?=[A-Z][a-z])|"
        r"(?<=[A-Z][A-Z])(?=[A-Z][a-z])|"
        r"(?<=[a-zA-Z])(?=\d)|"
        r"(?<=\d)(?=[a-zA-Z])"
    )
    return re.split(regex, s)


def make_snake_from_camel(camel_str: str) -> str:
    fragments = split_camel_case(camel_str)
    if not fragments:
        raise ValueError(f"Camel case string: {camel_str} cannot be split")
    return "_".join(f.lower() for f in fragments)
