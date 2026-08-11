import gzip
import json
from pathlib import Path

from app.core.config import settings

DEFAULT_HF_REPO = "xzm1999/XiaChuFang_Recipe_Corpus"
DEFAULT_FILE = "recipe_corpus_full.json"
DEFAULT_FILE_GZ = "recipe_corpus_full.json.gz"


def _data_dir() -> Path:
    return Path(settings.import_data_dir)


def download_dataset(sample_limit: int | None = None) -> Path:
    """Locate the XiaChuFang corpus locally (prefers .gz, then plain JSON).

    Returns a path to a readable JSON file. If only a .gz exists, it is
    decompressed into a temp file so the rest of the pipeline stays unchanged.
    """
    dest_dir = _data_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    gz_target = dest_dir / DEFAULT_FILE_GZ
    plain_target = dest_dir / DEFAULT_FILE

    if plain_target.exists():
        return plain_target

    if gz_target.exists():
        return _decompress(gz_target, dest_dir)

    # No full corpus: fall back to a small HF sample when sample_limit is set.
    if sample_limit and sample_limit <= 100:
        return _fetch_sample(sample_limit, plain_target)

    raise RuntimeError(
        f"Dataset file not found in {dest_dir}. Expected either "
        f"{DEFAULT_FILE} or {DEFAULT_FILE_GZ} (~1.8GB). Place it there, or "
        f"build/use the corpus data image (cookbook/corpus)."
    )


def _decompress(gz_path: Path, dest_dir: Path) -> Path:
    """Decompress a gz corpus once into the data dir, returning the plain path."""
    plain = dest_dir / DEFAULT_FILE
    if not plain.exists():
        with gzip.open(gz_path, "rb") as f_in, open(plain, "wb") as f_out:
            f_out.write(f_in.read())
    return plain


def _fetch_sample(sample_limit: int, target: Path) -> Path:
    """Fetch a small slice via the HF datasets-server API (dev/demo use)."""
    url = (
        f"https://datasets-server.huggingface.co/first-rows?dataset={DEFAULT_HF_REPO}"
        f"&config=default&split=train&offset=0&length={sample_limit}"
    )
    import httpx

    with httpx.Client(timeout=120) as client:
        resp = client.get(url)
        resp.raise_for_status()
        rows = resp.json()["rows"]
    data = [row["row"] for row in rows]
    target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return target


def iter_records(path: Path, sample_limit: int | None = None):
    """Yield recipe dicts from a JSON array file (or JSONL)."""
    with open(path, "r", encoding="utf-8") as f:
        head = f.read(1)
        f.seek(0)
        if head == "[":
            data = json.load(f)
            for i, rec in enumerate(data):
                if sample_limit and i >= sample_limit:
                    break
                yield rec
        else:
            for i, line in enumerate(f):
                if sample_limit and i >= sample_limit:
                    break
                line = line.strip()
                if line:
                    yield json.loads(line)
