import re

def strip_spaces(code: str) -> str:
    return code.replace(" ", "")

def normalize_punctuation(code: str) -> str:
    return re.sub(r"[^\w]", "-", code)

def lowercase(code: str) -> str:
    return code.lower()

def collapse_dashes(code: str) -> str:
    return re.sub(r"-+", "-", code)

def strip_dashes(code: str) -> str:
    return code.strip("-")

TRANSFORM_STEPS = [
    ("strip_spaces", strip_spaces),
    ("normalize_punctuation", normalize_punctuation),
    ("lowercase", lowercase),
    ("collapse_dashes", collapse_dashes),
    ("strip_dashes", strip_dashes)
]
