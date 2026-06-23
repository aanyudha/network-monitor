from __future__ import annotations

import asyncio

from app.core.models import PortCheckResult


class PortCheckEngine:
    async def check(self, ip_address: str, port: int, timeout_seconds: float = 1.5) -> PortCheckResult:
        try:
            connection = asyncio.open_connection(ip_address, port)
            reader, writer = await asyncio.wait_for(connection, timeout=timeout_seconds)
            writer.close()
            await writer.wait_closed()
            return PortCheckResult(port=port, is_open=True)
        except Exception as exc:
            return PortCheckResult(port=port, is_open=False, error=str(exc))

