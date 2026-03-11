from __future__ import annotations

import unittest

from app.services.rate_limiter import CompositeRateLimiter


class RateLimiterTest(unittest.TestCase):
    def test_rate_limiter_blocks_after_threshold(self) -> None:
        limiter = CompositeRateLimiter()
        limiter.burst.spec.user_limit = 2
        limiter.sustained.spec.user_limit = 1000
        limiter.burst.spec.ip_limit = 1000
        limiter.sustained.spec.ip_limit = 1000
        limiter.burst.spec.global_limit = 1000
        limiter.sustained.spec.global_limit = 1000

        limiter.enforce("u1", "127.0.0.1")
        limiter.enforce("u1", "127.0.0.1")

        with self.assertRaises(Exception):
            limiter.enforce("u1", "127.0.0.1")

    def test_no_partial_consumption_when_ip_limit_blocks(self) -> None:
        limiter = CompositeRateLimiter()
        limiter.burst.spec.user_limit = 100
        limiter.sustained.spec.user_limit = 100
        limiter.burst.spec.ip_limit = 1
        limiter.sustained.spec.ip_limit = 100
        limiter.burst.spec.global_limit = 100
        limiter.sustained.spec.global_limit = 100

        limiter.enforce("u1", "127.0.0.1")
        with self.assertRaises(Exception):
            limiter.enforce("u2", "127.0.0.1")

        # A different IP should still work if no partial global consumption occurred.
        limiter.enforce("u2", "127.0.0.2")


if __name__ == "__main__":
    unittest.main()
