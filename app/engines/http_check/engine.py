from __future__ import annotations

import asyncio
import time
from urllib import error, request

from app.core.models import HttpCheckResult


class HttpCheckEngine:
    async def check(self, url: str, keyword: str = "", timeout_seconds: float = 3.0) -> HttpCheckResult:
        return await asyncio.to_thread(self._run_sync_check, url, keyword, timeout_seconds)

    def _run_sync_check(self, url: str, keyword: str, timeout_seconds: float) -> HttpCheckResult:
        started = time.perf_counter()
        try:
            with request.urlopen(url, timeout=timeout_seconds) as response:
                body = response.read().decode(errors="ignore")
                elapsed = (time.perf_counter() - started) * 1000
                matched_keyword = keyword.lower() in body.lower() if keyword else True
                ok = 200 <= response.status < 400 and matched_keyword
                return HttpCheckResult(
                    ok=ok,
                    status_code=response.status,
                    response_ms=elapsed,
                    matched_keyword=matched_keyword,
                    error="" if ok else "Keyword not found" if not matched_keyword else "",
                )
        except error.HTTPError as exc:
            elapsed = (time.perf_counter() - started) * 1000
            return HttpCheckResult(ok=False, status_code=exc.code, response_ms=elapsed, error=str(exc))
        except Exception as exc:
            return HttpCheckResult(ok=False, status_code=None, response_ms=None, error=str(exc))

