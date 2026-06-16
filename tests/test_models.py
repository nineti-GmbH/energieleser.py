"""Tests for dataclass parsing and the value/unit helper."""

from __future__ import annotations

from typing import Any

import pytest

from energieleser import (
    DeviceType,
    EnergieleserUnknownDeviceError,
    GasleserDevice,
    Measurement,
    StromleserOneDevice,
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
    device = StromleserOneDevice.from_payload(stromleser_payload)

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
    device = StromleserOneDevice.from_payload(stromleser_single_phase_payload)

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
    assert device.signal_strength_dbm == -51.0


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


def test_waermeleser_from_payload(
    waermeleser_payload: dict[str, Any],
) -> None:
    device = WaermeleserDevice.from_payload(waermeleser_payload)

    assert device.device_type is DeviceType.WAERMELESER
    assert device.device_id == "HEAT_0000000001"
    assert device.timestamp == 1747285200
    assert device.total_energy_t1 == Measurement(value=34.09, unit="MWh")
    assert device.total_energy_t2 == Measurement(value=12.45, unit="MWh")
    assert device.total_energy_t3 == Measurement(value=5.67, unit="MWh")
    assert device.power == Measurement(value=2.31, unit="kW")
    assert device.total_volume == Measurement(value=3561.23, unit="m³")
    assert device.volume_flow == Measurement(value=1.23, unit="l/h")
    assert device.flow_temperature == Measurement(value=16.90, unit="°C")
    assert device.return_temperature == Measurement(value=19.60, unit="°C")
    assert device.temperature_difference == Measurement(value=2.68, unit="K")
    assert device.fabrication_number == "17580352"
    assert device.signal_strength_dbm == -51.0


@pytest.mark.parametrize(
    ("fixture_name", "expected_cls"),
    [
        ("stromleser_payload", StromleserOneDevice),
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


def test_parse_device_missing_device_id_raises() -> None:
    with pytest.raises(EnergieleserUnknownDeviceError) as excinfo:
        parse_device({"timestamp": 12345})
    assert excinfo.value.device_id == "unknown"


def test_zero_cumulative_totals_omitted() -> None:
    # 1. Stromleser
    strom_payload = {
        "device_id": "STROM_ONE_12345",
        "timestamp": "1776178480",
        "1.8.0": "0.000 Wh",          # cumulative -> should be skipped
        "1.8.1": "12.3 Wh",           # cumulative non-zero -> should not be skipped
        "2.8.0": "0.0 Wh",            # cumulative -> should be skipped
        "16.7.0": "0.000 W",          # non-cumulative zero -> should not be skipped
    }
    strom_device = StromleserOneDevice.from_payload(strom_payload)
    assert strom_device.energy_import is None
    assert strom_device.energy_export is None
    assert strom_device.energy_import_tariff_1 == Measurement(value=12.3, unit="Wh")
    assert strom_device.power_active == Measurement(value=0.0, unit="W")

    # 2. Gasleser
    gas_payload = {
        "device_id": "GAS_12345",
        "timestamp": "1776178480",
        "count": 10,
        "total_consumption": 0.0,     # cumulative -> should be skipped
        "current_flow_rate": 0.0,     # non-cumulative zero -> should not be skipped
    }
    gas_device = GasleserDevice.from_payload(gas_payload)
    assert gas_device.total_consumption is None
    assert gas_device.count == 10
    assert gas_device.current_flow_rate == 0.0

    # 3. Wasserleser
    wasser_payload = {
        "device_id": "WASSER_12345",
        "timestamp": "1776178480",
        "total_consumption": "0.000 m3",   # cumulative -> should be skipped
        "today_consumption": "0.000 m3",   # non-cumulative zero -> should not be skipped
        "current_flow_rate": "0 l/h",      # non-cumulative zero -> should not be skipped
    }
    wasser_device = WasserleserDevice.from_payload(wasser_payload)
    assert wasser_device.total_consumption is None
    assert wasser_device.today_consumption == Measurement(value=0.0, unit="m3")
    assert wasser_device.current_flow_rate == Measurement(value=0.0, unit="l/h")

    # 4. Waermeleser
    heat_payload = {
        "device_id": "HEAT_12345",
        "timestamp": "1776178480",
        "total_energy_t1": "0.00 MWh",     # cumulative -> should be skipped
        "total_energy_t2": "1.23 MWh",     # cumulative non-zero -> should not be skipped
        "total_energy_t3": "0.00 MWh",     # cumulative -> should be skipped
        "power": "0.00 kW",                # non-cumulative zero -> should not be skipped
        "total_volume": "0.00 m³",         # cumulative -> should be skipped
        "volume_flow": "0.00 l/h",         # non-cumulative zero -> should not be skipped
    }
    heat_device = WaermeleserDevice.from_payload(heat_payload)
    assert heat_device.total_energy_t1 is None
    assert heat_device.total_energy_t2 == Measurement(value=1.23, unit="MWh")
    assert heat_device.total_energy_t3 is None
    assert heat_device.power == Measurement(value=0.0, unit="kW")
    assert heat_device.total_volume is None
    assert heat_device.volume_flow == Measurement(value=0.0, unit="l/h")
