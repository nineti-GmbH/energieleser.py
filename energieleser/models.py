"""Data models and payload parsing for energieleser devices."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from energieleser.exceptions import EnergieleserUnknownDeviceError

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


class DeviceType(StrEnum):
    """Identifier for the four supported energieleser device families."""

    STROMLESER = "stromleser"
    GASLESER = "gasleser"
    WASSERLESER = "wasserleser"
    WAERMELESER = "waermeleser"


_PREFIX_MAP: dict[str, DeviceType] = {
    "STROM": DeviceType.STROMLESER,
    "GAS": DeviceType.GASLESER,
    "WASSER": DeviceType.WASSERLESER,
    "HEAT": DeviceType.WAERMELESER,
}


def detect_device_type(device_id: str) -> DeviceType:
    """Return the DeviceType matching the *device_id* prefix.

    Raises EnergieleserUnknownDeviceError when no prefix matches.
    """
    upper = device_id.upper()
    for prefix, dtype in _PREFIX_MAP.items():
        if upper.startswith(prefix):
            return dtype
    raise EnergieleserUnknownDeviceError(device_id)


def _parse_value_unit(raw: str) -> tuple[float, str]:
    """Split a "value unit" string into its parts.

    ``"8.160 W"`` becomes ``(8.16, "W")``; ``"-51"`` becomes ``(-51.0, "")``.
    """
    parts = raw.strip().split(maxsplit=1)
    value = float(parts[0])
    unit = parts[1].strip() if len(parts) > 1 else ""
    return value, unit


@dataclass(frozen=True, slots=True)
class Measurement:
    """A single measured value together with the unit the device reported."""

    value: float
    unit: str


def _measurement(payload: Mapping[str, Any], code: str) -> Measurement | None:
    """Parse one ``"value unit"`` field, ``None`` when the code is absent.

    Meters emit a dynamic subset of the OBIS schema depending on model and
    firmware configuration, so every code is treated as optional.
    """
    raw = payload.get(code)
    if raw is None:
        return None
    value, unit = _parse_value_unit(raw)
    return Measurement(value=value, unit=unit)


@dataclass(frozen=True, kw_only=True, slots=True)
class EnergieleserDevice:
    """Base type for a parsed device response."""

    device_id: str
    device_type: DeviceType
    timestamp: int


# OBIS measurement codes → semantic attribute name. Mirrors sml_schema.h:
# a meter emits a dynamic subset of these depending on model/firmware, so
# every entry is parsed only when present and left as ``None`` otherwise.
# Keep in sync with the firmware's SML/OBIS schema.
_STROMLESER_READINGS: dict[str, str] = {
    "1.8.0": "energy_import",
    "1.8.1": "energy_import_tariff_1",
    "1.8.2": "energy_import_tariff_2",
    "1.8.3": "energy_import_tariff_3",
    "1.8.4": "energy_import_tariff_4",
    "2.8.0": "energy_export",
    "2.8.1": "energy_export_tariff_1",
    "2.8.2": "energy_export_tariff_2",
    "2.8.3": "energy_export_tariff_3",
    "2.8.4": "energy_export_tariff_4",
    "16.7.0": "power_active",
    "15.7.0": "power_absolute",
    "1.7.0": "power_import",
    "2.7.0": "power_export",
    "36.7.0": "power_l1",
    "56.7.0": "power_l2",
    "76.7.0": "power_l3",
}


@dataclass(frozen=True, kw_only=True, slots=True)
class StromleserDevice(EnergieleserDevice):
    """Parsed response for a stromleser (electricity meter).

    Every OBIS-derived attribute is optional: meters report a dynamic subset
    of the schema, so a field is populated only when the meter sent its code
    and is ``None`` otherwise. Each measurement is a :class:`Measurement` carrying
    both the value and the unit the device reported (``Wh`` vs ``kWh`` etc.).
    """

    energy_import: Measurement | None = None
    energy_import_tariff_1: Measurement | None = None
    energy_import_tariff_2: Measurement | None = None
    energy_import_tariff_3: Measurement | None = None
    energy_import_tariff_4: Measurement | None = None
    energy_export: Measurement | None = None
    energy_export_tariff_1: Measurement | None = None
    energy_export_tariff_2: Measurement | None = None
    energy_export_tariff_3: Measurement | None = None
    energy_export_tariff_4: Measurement | None = None
    power_active: Measurement | None = None
    power_absolute: Measurement | None = None
    power_import: Measurement | None = None
    power_export: Measurement | None = None
    power_l1: Measurement | None = None
    power_l2: Measurement | None = None
    power_l3: Measurement | None = None
    signal_strength_dbm: float | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> StromleserDevice:
        """Build a StromleserDevice from whatever OBIS codes are present."""
        fields: dict[str, Any] = {
            attr: measurement
            for code, attr in _STROMLESER_READINGS.items()
            if (measurement := _measurement(payload, code)) is not None
        }
        # "16.7" is a firmware alias for "16.7.0"; only used as a fallback.
        if "power_active" not in fields and (alias := _measurement(payload, "16.7")):
            fields["power_active"] = alias
        rssi_dbm = payload.get("rssi")
        return cls(
            device_id=payload["device_id"],
            device_type=DeviceType.STROMLESER,
            timestamp=int(payload["timestamp"]),
            signal_strength_dbm=(
                _parse_value_unit(rssi_dbm)[0] if rssi_dbm is not None else None
            ),
            **fields,
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class GasleserDevice(EnergieleserDevice):
    """Parsed response for a gasleser (gas meter)."""

    count: int | None = None
    total_consumption: float | None = None
    current_flow_rate: float | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> GasleserDevice:
        """Build a GasleserDevice from whatever fields are present."""
        count = payload.get("count")
        total = payload.get("total_consumption")
        flow = payload.get("current_flow_rate")
        return cls(
            device_id=payload["device_id"],
            device_type=DeviceType.GASLESER,
            timestamp=int(payload["timestamp"]),
            count=int(count) if count is not None else None,
            total_consumption=float(total) if total is not None else None,
            current_flow_rate=float(flow) if flow is not None else None,
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class WasserleserDevice(EnergieleserDevice):
    """Parsed response for a wasserleser (water meter).

    Typed fields are TBD; the full payload is exposed under ``raw`` until the
    device's response shape is finalised.
    """

    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> WasserleserDevice:
        """Build a WasserleserDevice from the raw API JSON."""
        return cls(
            device_id=payload["device_id"],
            device_type=DeviceType.WASSERLESER,
            timestamp=int(payload["timestamp"]),
            raw=dict(payload),
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class WaermeleserDevice(EnergieleserDevice):
    """Parsed response for a wärmeleser (heat meter).

    Typed fields are TBD; the full payload is exposed under ``raw`` until the
    device's response shape is finalised.
    """

    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> WaermeleserDevice:
        """Build a WaermeleserDevice from the raw API JSON."""
        return cls(
            device_id=payload["device_id"],
            device_type=DeviceType.WAERMELESER,
            timestamp=int(payload["timestamp"]),
            raw=dict(payload),
        )


_DEVICE_BUILDERS: dict[DeviceType, Callable[[Mapping[str, Any]], EnergieleserDevice]] = {
    DeviceType.STROMLESER: StromleserDevice.from_payload,
    DeviceType.GASLESER: GasleserDevice.from_payload,
    DeviceType.WASSERLESER: WasserleserDevice.from_payload,
    DeviceType.WAERMELESER: WaermeleserDevice.from_payload,
}


def parse_device(payload: Mapping[str, Any]) -> EnergieleserDevice:
    """Detect the device type from *payload* and return its typed dataclass."""
    device_type = detect_device_type(payload["device_id"])
    return _DEVICE_BUILDERS[device_type](payload)
