"""Tests for ``EnergieleserClient``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import aiohttp
import pytest

from energieleser import (
    DeviceType,
    EnergieleserClient,
    EnergieleserConnectionError,
    EnergieleserTimeoutError,
    EnergieleserUnknownDeviceError,
    Measurement,
    StromleserOneDevice,
)

if TYPE_CHECKING:
    from aioresponses import aioresponses

HOST = "192.168.1.100"
BASE_URL = f"http://{HOST}/v1/data"


async def test_get_device_returns_stromleser(
    mock_http: aioresponses,
    stromleser_payload: dict[str, Any],
) -> None:
    mock_http.get(BASE_URL, payload=stromleser_payload)

    async with EnergieleserClient(HOST) as client:
        device = await client.get_device()

    assert isinstance(device, StromleserOneDevice)
    assert device.device_type is DeviceType.STROMLESER
    assert device.power_l3 == Measurement(value=8.16, unit="W")


async def test_get_device_returns_gasleser(
    mock_http: aioresponses,
    gasleser_payload: dict[str, Any],
) -> None:
    mock_http.get(BASE_URL, payload=gasleser_payload)

    async with EnergieleserClient(HOST) as client:
        device = await client.get_device()

    assert device.device_type is DeviceType.GASLESER
    assert device.timestamp == 1776179005


async def test_get_device_uses_custom_port(
    mock_http: aioresponses,
    gasleser_payload: dict[str, Any],
) -> None:
    mock_http.get(f"http://{HOST}:8080/v1/data", payload=gasleser_payload)

    async with EnergieleserClient(HOST, port=8080) as client:
        device = await client.get_device()

    assert device.device_type is DeviceType.GASLESER


async def test_get_device_raises_connection_error_on_http_500(
    mock_http: aioresponses,
) -> None:
    mock_http.get(BASE_URL, status=500)

    async with EnergieleserClient(HOST) as client:
        with pytest.raises(EnergieleserConnectionError):
            await client.get_device()


async def test_get_device_raises_connection_error_on_network_failure(
    mock_http: aioresponses,
) -> None:
    mock_http.get(BASE_URL, exception=aiohttp.ClientConnectionError("boom"))

    async with EnergieleserClient(HOST) as client:
        with pytest.raises(EnergieleserConnectionError):
            await client.get_device()


async def test_get_device_raises_timeout_error(mock_http: aioresponses) -> None:
    mock_http.get(BASE_URL, exception=TimeoutError())

    async with EnergieleserClient(HOST, request_timeout=0.1) as client:
        with pytest.raises(EnergieleserTimeoutError):
            await client.get_device()


async def test_get_device_raises_unknown_device_for_bad_prefix(
    mock_http: aioresponses,
) -> None:
    mock_http.get(BASE_URL, payload={"device_id": "FOO_1", "timestamp": "1"})

    async with EnergieleserClient(HOST) as client:
        with pytest.raises(EnergieleserUnknownDeviceError):
            await client.get_device()


async def test_context_manager_closes_internally_owned_session(
    mock_http: aioresponses,
    stromleser_payload: dict[str, Any],
) -> None:
    mock_http.get(BASE_URL, payload=stromleser_payload)

    client = EnergieleserClient(HOST)
    async with client:
        await client.get_device()

    assert client._session is None  # noqa: SLF001 — verifying internal state


async def test_external_session_is_not_closed(
    mock_http: aioresponses,
    stromleser_payload: dict[str, Any],
) -> None:
    mock_http.get(BASE_URL, payload=stromleser_payload)

    session = aiohttp.ClientSession()
    try:
        client = EnergieleserClient(HOST, session=session)
        async with client:
            await client.get_device()
        assert not session.closed
    finally:
        await session.close()
