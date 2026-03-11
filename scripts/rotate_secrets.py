#!/usr/bin/env python
from __future__ import annotations

import base64
import json
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet


def main() -> None:
    fernet_key = os.getenv("RIA_SECRETS_ENCRYPTION_KEY")
    if not fernet_key:
        # Emit a one-time key when not provided.
        fernet_key = Fernet.generate_key().decode("utf-8")
        print("Generated new RIA_SECRETS_ENCRYPTION_KEY. Store this securely:")
        print(fernet_key)

    cipher = Fernet(fernet_key.encode("utf-8"))

    rotated = {
        "RIA_INTERNAL_API_TOKEN": secrets.token_urlsafe(48),
        "RIA_AUDIT_SIGNING_KEY": secrets.token_urlsafe(64),
    }
    plaintext = json.dumps(rotated, indent=2).encode("utf-8")
    encrypted = cipher.encrypt(plaintext)

    out_path = Path("deploy/k8s/secrets.rotated.enc")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(encrypted)

    print(f"Encrypted rotated secrets written to {out_path}")


if __name__ == "__main__":
    main()
