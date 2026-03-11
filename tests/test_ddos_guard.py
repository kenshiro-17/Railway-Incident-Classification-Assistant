from __future__ import annotations

import unittest

from app.core.config import settings
from app.services.ddos_guard import DDoSGuard


class DDoSGuardTest(unittest.TestCase):
    def test_block_after_repeated_violations(self) -> None:
        guard = DDoSGuard()
        ip = "10.0.0.10"
        for _ in range(settings.ddos_block_after_violations):
            guard.record_violation(ip)
        blocked_for = guard.is_blocked(ip)
        self.assertGreater(blocked_for, 0)


if __name__ == "__main__":
    unittest.main()
