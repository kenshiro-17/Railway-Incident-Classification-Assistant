from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.core.security import require_user


class SecurityAuthTest(unittest.TestCase):
    def test_require_user_rejects_missing_bearer(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            require_user("")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_require_user_accepts_stub_token(self) -> None:
        user = require_user("Bearer user:alice|role:worker")
        self.assertEqual(user.user_id, "alice")
        self.assertEqual(user.role, "worker")

    def test_prod_requires_jwt_mode_when_enforced(self) -> None:
        with patch("app.core.security.settings.environment", "prod"), patch(
            "app.core.security.settings.require_jwt_in_prod", True
        ), patch("app.core.security.settings.sso_mode", "stub"):
            with self.assertRaises(HTTPException) as ctx:
                require_user("Bearer user:alice|role:worker")
            self.assertEqual(ctx.exception.status_code, 500)


if __name__ == "__main__":
    unittest.main()
