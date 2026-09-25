"""Latest firmware versions published by the energieleser OTA server."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from aiohttp import ClientError, ContentTypeError

from energieleser.exceptions import (
    EnergieleserConnectionError,
    EnergieleserParsingError,
    EnergieleserTimeoutError,
)
from energieleser.models import DeviceType

if TYPE_CHECKING:
    import aiohttp

LATEST_VERSIONS_URL = "https://api.energieleser.com/devices/v4/ota/latest-versions"

_LOGGER = logging.getLogger(__name__)

# OTA server keys differ from DeviceType values.
_OTA_KEYS: dict[DeviceType, str] = {
    DeviceType.STROMLESER: "stromleser",
    DeviceType.GASLESER: "gasleser-8mb",
    DeviceType.GASLESER_PULSE: "gasleser-pulse",
    DeviceType.WASSERLESER: "wasserleser",
    DeviceType.WAERMELESER: "heat",
}

# Suffixes like git-describe's "-31-g1658863" are ignored.
_VERSION_RE = re.compile(r"v?(\d+(?:\.\d+)*)")


def _parse_version(version: str) -> tuple[int, ...] | None:
    """Return the numeric parts of *version*, ``None`` when unparseable."""
    match = _VERSION_RE.match(version.strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def _pad(parts: tuple[int, ...], width: int) -> tuple[int, ...]:
    return parts + (0,) * (width - len(parts))


def is_newer_version(installed: str, latest: str) -> bool:
    """Return True if *latest* is newer than *installed*; False if either is unparseable."""
    installed_parts = _parse_version(installed)
    latest_parts = _parse_version(latest)
    if installed_parts is None or latest_parts is None:
        return False
    width = max(len(installed_parts), len(latest_parts))
    return _pad(latest_parts, width) > _pad(installed_parts, width)


async def get_latest_firmware_versions(
    session: aiohttp.ClientSession,
    *,
    request_timeout: float = 10.0,
) -> dict[DeviceType, str]:
    """Return the latest published firmware version per device type."""
    try:
        async with asyncio.timeout(request_timeout):
            response = await session.get(LATEST_VERSIONS_URL)
            response.raise_for_status()
            payload: object = await response.json()
    except TimeoutError as err:
        msg = f"Timed out reading {LATEST_VERSIONS_URL}"
        raise EnergieleserTimeoutError(msg) from err
    except (ContentTypeError, ValueError) as err:
        msg = f"Invalid JSON from {LATEST_VERSIONS_URL}: {err}"
        raise EnergieleserParsingError(msg) from err
    except ClientError as err:
        msg = f"Failed to reach {LATEST_VERSIONS_URL}: {err}"
        raise EnergieleserConnectionError(msg) from err

    if not isinstance(payload, dict):
        msg = f"Expected a JSON object, got {type(payload).__name__}"
        raise EnergieleserParsingError(msg)

    versions: dict[DeviceType, str] = {}
    for device_type, key in _OTA_KEYS.items():
        version = payload.get(key)
        if isinstance(version, str):
            versions[device_type] = version
        elif version is not None:
            _LOGGER.debug("Ignoring non-string version for '%s': %s", key, version)
    return versions
