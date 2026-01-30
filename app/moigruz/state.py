import json
import os


def load_seen_ids(state_file: str) -> set[str]:
    if not os.path.exists(state_file):
        return set()
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        ids = data.get("seen_ids", [])
        return set(str(x) for x in ids if x)
    except Exception:
        return set()


def save_seen_ids(state_file: str, seen_ids: set[str]) -> None:
    os.makedirs(os.path.dirname(state_file) or ".", exist_ok=True)
    data = {"seen_ids": sorted(seen_ids)}
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


