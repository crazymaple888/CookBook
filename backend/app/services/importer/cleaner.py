import re

from app.utils.text import fullwidth_to_halfwidth

_UNITS = [
    "千克", "公斤", "毫升", "克", "斤", "升", "勺", "根", "片", "条", "个", "只",
    "块", "粒", "颗", "瓣", "枚", "杯", "碗", "把", "份", "汤匙", "茶匙", "滴",
    "适量", "少许", "若干", "一点", "袋", "包", "听", "罐", "朵", "小把", "汤勺",
    "匙", "撮", "层", "段", "茶勺", "汤匙",
]

# English unit abbreviations common in the corpus (200g, 10ml, 1kg, 5L).
_EN_UNITS = ["kg", "g", "ml", "l", "tbsp", "tsp", "oz", "lb"]

_DESCRIPTORS = [
    "大片", "小片", "大块", "小块", "大根", "小根", "大把", "小把", "大个", "小个",
    "大条", "小条", "大瓣", "小瓣", "大", "小", "新鲜", "冷冻", "熟的", "生的",
    "切好的", "洗净的", "干", "湿", "去壳", "去骨", "去皮",
]

_NOISE_PATTERNS = [
    re.compile(r"[【\[\(（][^】\]\)）]*[】\]\)）]"),
    re.compile(r"\(.*?\)"),
    re.compile(r"[a-zA-Z]+"),
    re.compile(r"适量|少许|若干|一点|任意|随意"),
    re.compile(r"\d+-\d+"),
]

_PREP_SUFFIXES = [
    "切成丁", "切成末", "切成丝", "切成块", "切成片", "切成段", "切成条", "切成",
    "切末", "切丝", "切块", "切片", "切段", "切丁", "切条", "剁碎", "拍碎",
    "洗净", "去皮", "去核", "焯水", "打散", "切好", "备好", "切碎",
    "切滚刀块", "切小丁", "切小片",
]

_META_PREFIXES = ["做法", "步骤", "准备", "备注", "贴士", "小贴士", "提示", "调味料", "辅料"]

# digit + optional unit pattern for extracting quantity/unit from anywhere.
_CN_UNIT_GROUP = "克|千克|公斤|毫升|斤|升|勺|根|片|条|个|只|块|粒|颗|瓣|枚|杯|碗|把|份|汤匙|茶匙|滴|袋|包|听|罐|朵|小把|汤勺|匙|撮|层|段|茶勺|小勺|大勺"
_QTY_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?|[一二三四五六七八九十两半]+)(" + _CN_UNIT_GROUP + r"|kg|g|ml|l|tbsp|tsp|oz|lb)"
)
# "2大片生菜", "1-2个小的红萝卜", "半个洋葱": digits [+ desc] + unit, possibly with range.
_QTY_DESC_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?|[一二三四五六七八九十两半]+)"
    r"(?:-\d+)?"
    r"(?:[大中小])?"
    r"(" + _CN_UNIT_GROUP + r")"
)
_LEAD_QTY_DESC_UNIT_RE = re.compile(r"^\d+(?:\.\d+)?|[一二三四五六七八九十两半]+(?:[大中小])?(" + _CN_UNIT_GROUP + r")")


def parse_ingredient_line(raw: str) -> list[dict]:
    """Parse messy corpus ingredient text into one or more clean ingredients.

    Returns a list (usually length 1). Comma-separated multi-ingredient lines
    ('适量橄榄油，盐，黑胡椒') split into separate entries. Pure decoration
    yields an entry with name=''.
    """
    # Strip NUL and other illegal control characters PostgreSQL rejects.
    raw_clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw)
    cleaned = fullwidth_to_halfwidth(raw_clean).strip()
    if not cleaned:
        return [{"name": "", "quantity": None, "unit": None, "raw_text": raw_clean}]

    # Split multi-ingredient lines on Chinese/ASCII commas and slashes.
    parts = [p.strip() for p in re.split(r"[，,、/；;]+", cleaned) if p.strip()]
    if not parts:
        return [{"name": "", "quantity": None, "unit": None, "raw_text": raw_clean}]
    if len(parts) > 1:
        return [parse_ingredient_line(p)[0] for p in parts]

    cleaned = parts[0]

    # Extract quantity+unit FIRST, before noise stripping, so English units
    # (200g, 10ml) survive long enough to be removed with their number.
    quantity = None
    unit = None
    m = _QTY_UNIT_RE.search(cleaned)
    if m:
        qty_str, unit = m.group(1), m.group(2)
        try:
            quantity = float(qty_str)
        except ValueError:
            quantity = None
        cleaned = (cleaned[: m.start()] + " " + cleaned[m.end():]).strip()
    else:
        # Handle '1-2个小的红萝卜' / '2大片生菜'
        m2 = _QTY_DESC_UNIT_RE.match(cleaned)
        if m2:
            unit = m2.group(2)
            try:
                quantity = float(m2.group(1))
            except ValueError:
                quantity = None
            cleaned = cleaned[m2.end():].strip()

    for pat in _NOISE_PATTERNS:
        cleaned = pat.sub("", cleaned)
    cleaned = cleaned.strip(" ，,、.:：;；")

    for prefix in _META_PREFIXES:
        if cleaned.startswith(prefix):
            return [{"name": "", "quantity": None, "unit": None, "raw_text": raw_clean}]

    if not cleaned:
        return [{"name": "", "quantity": None, "unit": None, "raw_text": raw_clean}]

    # Strip a stray leading unit word left by range parsing ('个小的红萝卜' -> '小的红萝卜').
    for u in sorted(_UNITS, key=len, reverse=True):
        if cleaned.startswith(u) and len(cleaned) > len(u):
            cleaned = cleaned[len(u):].strip()
            break

    for desc in _DESCRIPTORS:
        if cleaned.startswith(desc):
            cleaned = cleaned[len(desc):].strip()
            break
    for desc in _DESCRIPTORS:
        if cleaned.endswith(desc):
            cleaned = cleaned[: -len(desc)].strip()
            break

    for suffix in sorted(_PREP_SUFFIXES, key=len, reverse=True):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
            break

    cleaned = cleaned.strip(" ，,、.:：;；-_的")

    if not is_valid_ingredient_name(cleaned):
        return [{"name": "", "quantity": quantity, "unit": unit, "raw_text": raw_clean}]

    return [{"name": cleaned, "quantity": quantity, "unit": unit, "raw_text": raw_clean}]


def is_valid_ingredient_name(name: str) -> bool:
    """Return False for corpus noise that is not a real ingredient name.

    Filters section headers (#主料), long descriptions, stray quantities,
    sentences with connectors, and strings without meaningful Chinese text.
    """
    if not name:
        return False
    # Section headers / meta like "# 主料", "做法：", "辅料"
    if name.startswith("#") or name.startswith("做法") or name.startswith("步骤"):
        return False
    # Long descriptive strings are almost never a single ingredient.
    if len(name) > 12:
        return False
    # Sentences with connectors/alternatives.
    if any(k in name for k in ("或", "或者", " 和 ", "、", "，", "，", "具体", "文字", "看下面")):
        return False
    # Must contain meaningful Chinese characters.
    if not re.search(r"[一-鿿]", name):
        return False
    # Pure digits/units like "100克" with no food name after cleaning.
    if not re.search(r"[一-鿿]", name.replace("克", "").replace("个", "").replace("片", "")):
        return False
    return True
