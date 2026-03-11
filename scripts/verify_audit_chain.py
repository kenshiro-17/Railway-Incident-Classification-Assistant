from __future__ import annotations

import hashlib
import json
from pathlib import Path


def verify_chain(path: Path) -> bool:
    previous_hash = "genesis"
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        event = json.loads(raw)
        prev = event.get("prev_hash", "genesis")
        entry_hash = event.get("entry_hash")
        if prev != previous_hash:
            return False
        reconstructed = dict(event)
        reconstructed.pop("entry_hash", None)
        payload = json.dumps(reconstructed, ensure_ascii=True, sort_keys=True)
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if expected != entry_hash:
            return False
        previous_hash = entry_hash
    return True


def main() -> None:
    path = Path("app/data/audit.log")
    if not path.exists():
        raise SystemExit("Audit log not found")
    ok = verify_chain(path)
    if not ok:
        raise SystemExit("Audit chain verification failed")
    print("Audit chain verification passed")


if __name__ == "__main__":
    main()
