"""Tests for ``EnergieleserClient``."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from energieleser import (
    DeviceType,
    EnergieleserClient,
    EnergieleserConnectionError,
    EnergieleserParsingError,
    EnergieleserTimeoutError,
    EnergieleserUnknownDeviceError,
    Measurement,
    StromleserOneDevice,
)

HOST = "192.168.1.100"
BASE_URL = f"http://{HOST}/v1/data"


async def test_get_device_returns_stromleser(
    stromleser_payload: dict[str, Any],
) -> None:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.json = AsyncMock(return_value=stromleser_payload)
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)

    async with EnergieleserClient(HOST, session=mock_session) as client:
        device = await client.get_device()

    assert isinstance(device, StromleserOneDevice)
    assert device.device_type is DeviceType.STROMLESER
    assert device.power_l3 == Measurement(value=8.16, unit="W")
    mock_session.get.assert_called_once_with(BASE_URL)


async def test_get_device_returns_gasleser(
    gasleser_payload: dict[str, Any],
) -> None:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.json = AsyncMock(return_value=gasleser_payload)
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)

    async with EnergieleserClient(HOST, session=mock_session) as client:
        device = await client.get_device()

    assert device.device_type is DeviceType.GASLESER
    assert device.timestamp == 1776179005
    mock_session.get.assert_called_once_with(BASE_URL)


async def test_get_device_uses_custom_port(
    gasleser_payload: dict[str, Any],
) -> None:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.json = AsyncMock(return_value=gasleser_payload)
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)

    async with EnergieleserClient(HOST, port=8080, session=mock_session) as client:
        device = await client.get_device()

    assert device.device_type is DeviceType.GASLESER
    mock_session.get.assert_called_once_with(f"http://{HOST}:8080/v1/data")


async def test_get_device_raises_connection_error_on_http_500() -> None:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=500,
    )
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)

    async with EnergieleserClient(HOST, session=mock_session) as client:
        with pytest.raises(EnergieleserConnectionError):
            await client.get_device()


async def test_get_device_raises_connection_error_on_network_failure() -> None:
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get.side_effect = aiohttp.ClientConnectionError("boom")

    async with EnergieleserClient(HOST, session=mock_session) as client:
        with pytest.raises(EnergieleserConnectionError):
            await client.get_device()


async def test_get_device_raises_timeout_error() -> None:
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get.side_effect = TimeoutError()

    async with EnergieleserClient(HOST, request_timeout=0.1, session=mock_session) as client:
        with pytest.raises(EnergieleserTimeoutError):
            await client.get_device()


async def test_get_device_raises_unknown_device_for_bad_prefix() -> None:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.json = AsyncMock(return_value={"device_id": "FOO_1", "timestamp": "1"})
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)

    async with EnergieleserClient(HOST, session=mock_session) as client:
        with pytest.raises(EnergieleserUnknownDeviceError):
            await client.get_device()


async def test_get_device_raises_parsing_error_for_malformed_payload() -> None:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.json = AsyncMock(return_value={"device_id": "STROM_ONE_8529546829"})
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)

    async with EnergieleserClient(HOST, session=mock_session) as client:
        with pytest.raises(EnergieleserParsingError):
            await client.get_device()


async def test_context_manager_closes_internally_owned_session(
    stromleser_payload: dict[str, Any],
) -> None:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.json = AsyncMock(return_value=stromleser_payload)
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client = EnergieleserClient(HOST)
        async with client:
            await client.get_device()

    assert client._session is None  # noqa: SLF001 — verifying internal state
    mock_session.close.assert_called_once()


async def test_external_session_is_not_closed(
    stromleser_payload: dict[str, Any],
) -> None:
    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.json = AsyncMock(return_value=stromleser_payload)
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.closed = False

    client = EnergieleserClient(HOST, session=mock_session)
    async with client:
        await client.get_device()
    assert not mock_session.closed
    mock_session.close.assert_not_called()
