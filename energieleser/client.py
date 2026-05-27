"""Async HTTP client for energieleser devices."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Self

import aiohttp
from aiohttp import ClientError

from energieleser.exceptions import (
    EnergieleserConnectionError,
    EnergieleserTimeoutError,
)
from energieleser.models import EnergieleserDevice, parse_device

if TYPE_CHECKING:
    from types import TracebackType

DEFAULT_PORT = 80

_LOGGER = logging.getLogger(__name__)


class EnergieleserClient:
    """Async client for an energieleser device's local HTTP API."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        *,
        session: aiohttp.ClientSession | None = None,
        request_timeout: float = 10.0,
    ) -> None:
        """Initialise the client.

        When ``session`` is omitted, the client lazily creates its own
        :class:`aiohttp.ClientSession` and closes it on :meth:`close` /
        ``__aexit__``. Externally supplied sessions are never closed by the
        client — the caller owns their lifecycle.
        """
        self._host = host
        self._port = port
        self._request_timeout = request_timeout
        self._session = session
        self._owns_session = session is None

        _LOGGER.debug("Initialized client for %s:%s", self._host, self._port)

    @property
    def base_url(self) -> str:
        """Return the device's JSON data endpoint URL.

        The port is omitted when it is the HTTP default (80), so the URL
        matches the device's advertised address exactly.
        """
        host = self._host if self._port == DEFAULT_PORT else f"{self._host}:{self._port}"
        return f"http://{host}/v1/data"

    async def get_device(self) -> EnergieleserDevice:
        """Fetch the device JSON and return its typed dataclass."""
        session = await self._ensure_session()
        try:
            async with asyncio.timeout(self._request_timeout):
                response = await session.get(self.base_url)
                response.raise_for_status()
                payload: dict[str, Any] = await response.json()
                _LOGGER.debug("Received data from device: %s", payload)
        except TimeoutError as err:
            _LOGGER.debug("Timed out reading %s", self._host)
            msg = f"Timed out reading {self.base_url}"
            raise EnergieleserTimeoutError(msg) from err
        except ClientError as err:
            _LOGGER.debug("Error connecting to %s: %s", self._host, err)
            msg = f"Failed to reach {self.base_url}: {err}"
            raise EnergieleserConnectionError(msg) from err

        try:
            device = parse_device(payload)
        except Exception:
            _LOGGER.exception(
                "Failed to parse device payload from %s.",
                self._host,
            )
            raise

        _LOGGER.debug("Successfully parsed %s device: %s", device.device_id, device)
        return device

    async def close(self) -> None:
        """Close the internally-owned session, if any."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> Self:
        """Enter the async context, ensuring a session exists."""
        await self._ensure_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the internally-owned session on context exit."""
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
