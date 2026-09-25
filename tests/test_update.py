"""Tests for ``energieleser.update``."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from energieleser import (
    LATEST_VERSIONS_URL,
    DeviceType,
    EnergieleserConnectionError,
    EnergieleserParsingError,
    EnergieleserTimeoutError,
    get_latest_firmware_versions,
    is_newer_version,
)

API_RESPONSE: dict[str, Any] = {
    "stromleser": "v1.4.30",
    "gasleser-8mb": "v1.5.35",
    "wasserleser": "v1.6.4",
    "heat": "v1.2.4",
    "gasleser-pulse": "v1.0.5",
}


def _session_returning(payload: Any) -> MagicMock:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.json = AsyncMock(return_value=payload)
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)
    return mock_session


@pytest.mark.parametrize(
    ("installed", "latest", "expected"),
    [
        pytest.param("v1.4.22", "v1.4.30", True, id="older_patch"),
        pytest.param("1.4.22", "v1.4.30", True, id="mixed_v_prefix"),
        pytest.param("v1.9.0", "v1.10.0", True, id="numeric_not_lexical"),
        pytest.param("v1.4", "v1.4.1", True, id="shorter_installed"),
        pytest.param("v1.4.22-31-g1658863", "v1.4.30", True, id="dev_build_older"),
        pytest.param(" v1.4.22 ", "v1.4.30", True, id="whitespace"),
        pytest.param("v1.4.30", "v1.4.30", False, id="equal"),
        pytest.param("v1.4.30", "1.4.30", False, id="equal_mixed_prefix"),
        pytest.param("v1.4", "v1.4.0", False, id="equal_zero_padded"),
        pytest.param("v1.4.31", "v1.4.30", False, id="installed_newer"),
        pytest.param("v1.4.30-2-gabcdef0", "v1.4.30", False, id="dev_build_same_base"),
        pytest.param("garbage", "v1.4.30", False, id="unparseable_installed"),
        pytest.param("v1.4.30", "", False, id="unparseable_latest"),
    ],
)
def test_is_newer_version(installed: str, latest: str, expected: bool) -> None:
    assert is_newer_version(installed, latest) is expected


async def test_get_latest_firmware_versions_maps_all_types() -> None:
    session = _session_returning(API_RESPONSE)

    versions = await get_latest_firmware_versions(session)

    assert versions == {
        DeviceType.STROMLESER: "v1.4.30",
        DeviceType.GASLESER: "v1.5.35",
        DeviceType.GASLESER_PULSE: "v1.0.5",
        DeviceType.WASSERLESER: "v1.6.4",
        DeviceType.WAERMELESER: "v1.2.4",
    }
    session.get.assert_called_once_with(LATEST_VERSIONS_URL)


async def test_get_latest_firmware_versions_ignores_unknown_and_missing() -> None:
    session = _session_returning({"stromleser": "v1.4.30", "toaster": "v9.9.9"})

    versions = await get_latest_firmware_versions(session)

    assert versions == {DeviceType.STROMLESER: "v1.4.30"}


async def test_get_latest_firmware_versions_skips_non_string_values() -> None:
    session = _session_returning({"stromleser": 1430, "heat": "v1.2.4"})

    versions = await get_latest_firmware_versions(session)

    assert versions == {DeviceType.WAERMELESER: "v1.2.4"}


async def test_get_latest_firmware_versions_rejects_non_object() -> None:
    session = _session_returning(["v1.4.30"])

    with pytest.raises(EnergieleserParsingError):
        await get_latest_firmware_versions(session)


async def test_get_latest_firmware_versions_rejects_invalid_json() -> None:
    session = _session_returning(None)
    session.get.return_value.json.side_effect = ValueError("bad json")

    with pytest.raises(EnergieleserParsingError):
        await get_latest_firmware_versions(session)


async def test_get_latest_firmware_versions_rejects_wrong_content_type() -> None:
    session = _session_returning(None)
    session.get.return_value.json.side_effect = aiohttp.ContentTypeError(
        request_info=MagicMock(), history=()
    )

    with pytest.raises(EnergieleserParsingError):
        await get_latest_firmware_versions(session)


async def test_get_latest_firmware_versions_http_error() -> None:
    session = _session_returning(API_RESPONSE)
    session.get.return_value.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=(), status=500
    )

    with pytest.raises(EnergieleserConnectionError):
        await get_latest_firmware_versions(session)


async def test_get_latest_firmware_versions_connection_error() -> None:
    session = _session_returning(API_RESPONSE)
    session.get.side_effect = aiohttp.ClientConnectionError("down")

    with pytest.raises(EnergieleserConnectionError):
        await get_latest_firmware_versions(session)


async def test_get_latest_firmware_versions_timeout() -> None:
    session = _session_returning(API_RESPONSE)
    session.get.side_effect = TimeoutError

    with pytest.raises(EnergieleserTimeoutError):
        await get_latest_firmware_versions(session)
