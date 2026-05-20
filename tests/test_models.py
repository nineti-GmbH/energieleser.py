"""Tests for dataclass parsing and the value/unit helper."""

from __future__ import annotations

from typing import Any

import pytest

from energieleser import (
    DeviceType,
    GasleserDevice,
    Measurement,
    StromleserDevice,
    WaermeleserDevice,
    WasserleserDevice,
    parse_device,
)
from energieleser.models import _parse_value_unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("8.160 W", (8.16, "W")),
        ("12345.000 Wh", (12345.0, "Wh")),
        ("84 %", (84.0, "%")),
        ("-51", (-51.0, "")),
        ("  0.000 kW  ", (0.0, "kW")),
    ],
)
def test_parse_value_unit(raw: str, expected: tuple[float, str]) -> None:
    assert _parse_value_unit(raw) == expected


def test_parse_value_unit_raises_on_garbage() -> None:
    with pytest.raises(ValueError, match="could not convert"):
        _parse_value_unit("not-a-number")


def test_stromleser_from_payload(stromleser_payload: dict[str, Any]) -> None:
    device = StromleserDevice.from_payload(stromleser_payload)

    assert device.device_id == "STROM_ONE_8529546829"
    assert device.device_type is DeviceType.STROMLESER
    assert device.timestamp == 1776178480
    assert device.energy_import == Measurement(value=12345.0, unit="Wh")
    assert device.energy_export == Measurement(value=26561.0, unit="Wh")
    assert device.power_active == Measurement(value=8.16, unit="W")
    assert device.power_l1 == Measurement(value=0.0, unit="W")
    assert device.power_l2 == Measurement(value=0.0, unit="W")
    assert device.power_l3 == Measurement(value=8.16, unit="W")
    assert device.signal_strength_dbm == -51.0
    # Codes the meter did not send stay None instead of raising.
    assert device.energy_import_tariff_1 is None
    assert device.energy_export_tariff_2 is None


def test_stromleser_single_phase_omits_per_phase_power(
    stromleser_single_phase_payload: dict[str, Any],
) -> None:
    device = StromleserDevice.from_payload(stromleser_single_phase_payload)

    assert device.device_id == "STROM_ONE_2429489063"
    assert device.energy_import == Measurement(value=45.167, unit="kWh")
    assert device.energy_import_tariff_1 == Measurement(value=45.167, unit="kWh")
    assert device.energy_export == Measurement(value=19929.796, unit="kWh")
    assert device.energy_export_tariff_1 == Measurement(value=19929.796, unit="kWh")
    assert device.power_active == Measurement(value=5.0, unit="W")
    # This meter sends no per-phase registers; they must be None, not errors.
    assert device.power_l1 is None
    assert device.power_l2 is None
    assert device.power_l3 is None
    assert device.signal_strength_dbm == -42.0


def test_gasleser_from_payload(gasleser_payload: dict[str, Any]) -> None:
    device = GasleserDevice.from_payload(gasleser_payload)

    assert device.device_id == "GAS_8530321017"
    assert device.device_type is DeviceType.GASLESER
    assert device.timestamp == 1776179005
    assert device.count == 603
    assert device.total_consumption == pytest.approx(37030.67)
    assert device.current_flow_rate == pytest.approx(0.01)


def test_wasserleser_from_payload(
    wasserleser_payload: dict[str, Any],
) -> None:
    device = WasserleserDevice.from_payload(wasserleser_payload)

    assert device.device_type is DeviceType.WASSERLESER
    assert device.device_id == "WASSER_0499632826"
    assert device.timestamp == 1779276532
    assert device.total_consumption == Measurement(value=123.755, unit="m3")
    assert device.today_consumption == Measurement(value=0.0, unit="m3")
    assert device.current_flow_rate == Measurement(value=0.0, unit="l/h")
    assert device.current_flow_rate_m3 == Measurement(value=0.0, unit="m3/h")
    assert device.signal_strength_dbm == -49.0


def test_waermeleser_from_payload_exposes_raw(
    waermeleser_payload: dict[str, Any],
) -> None:
    device = WaermeleserDevice.from_payload(waermeleser_payload)

    assert device.device_type is DeviceType.WAERMELESER
    assert device.device_id == "HEAT_0000000001"
    assert device.raw == waermeleser_payload


@pytest.mark.parametrize(
    ("fixture_name", "expected_cls"),
    [
        ("stromleser_payload", StromleserDevice),
        ("gasleser_payload", GasleserDevice),
        ("wasserleser_payload", WasserleserDevice),
        ("waermeleser_payload", WaermeleserDevice),
    ],
)
def test_parse_device_dispatches_by_prefix(
    fixture_name: str,
    expected_cls: type,
    request: pytest.FixtureRequest,
) -> None:
    payload = request.getfixturevalue(fixture_name)
    device = parse_device(payload)
    assert isinstance(device, expected_cls)
