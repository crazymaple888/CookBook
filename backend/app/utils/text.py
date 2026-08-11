import re

_UNIT_WORDS = [
    "千克", "公斤", "毫升", "克", "斤", "升", "勺", "根", "片", "条", "个", "只",
    "块", "粒", "颗", "瓣", "枚", "杯", "碗", "把", "份", "汤匙", "茶匙", "滴",
    "适量", "少许", "若干", "一点",
]
_UNIT_RE = re.compile(
    r"^(?P<name>.*?)(?P<qty>[0-9]+(?:\.[0-9]+)?|[一二三四五六七八九十两半]+)?"
    r"(?P<unit>" + "|".join(sorted(_UNIT_WORDS, key=len, reverse=True)) + r")$"
)


def fullwidth_to_halfwidth(text: str) -> str:
    out = []
    for ch in text:
        code = ord(ch)
        if code == 0x3000:
            code = 0x20
        elif 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        out.append(chr(code))
    return "".join(out)


def normalize_name(text: str) -> str:
    return fullwidth_to_halfwidth(text).strip().lower()


def strip_unit_suffix(name: str) -> tuple[str, str | None]:
    """Strip quantity+unit suffix like '猪肉500克', returning (clean_name, unit_or_None)."""
    cleaned = fullwidth_to_halfwidth(name).strip()
    match = _UNIT_RE.match(cleaned)
    if match and match.group("name"):
        return match.group("name"), match.group("unit")
    return cleaned, None
