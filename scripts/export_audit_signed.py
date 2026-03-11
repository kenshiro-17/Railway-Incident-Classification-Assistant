from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    key = os.getenv("RIA_AUDIT_SIGNING_KEY", "")
    if not key:
        raise SystemExit("Missing RIA_AUDIT_SIGNING_KEY")

    source = Path("app/data/audit.log")
    if not source.exists():
        raise SystemExit("Audit log not found")

    payload = source.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    signature = hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "sha256": digest,
        "hmac_sha256": signature,
    }

    out_path = Path("app/data/audit_export_signature.json")
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Signed audit export written to {out_path}")


if __name__ == "__main__":
    main()
