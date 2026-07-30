"""Data models and payload parsing for energieleser devices."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from energieleser.exceptions import EnergieleserUnknownDeviceError

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

_LOGGER = logging.getLogger(__name__)
_LOGGED_UNITLESS: set[tuple[str, str]] = set()


class DeviceType(StrEnum):
    """Device type identifier used in API responses and manifests."""

    STROMLESER = "stromleser"
    GASLESER = "gasleser"
    GASLESER_PULSE = "gasleser.pulse"
    WASSERLESER = "wasserleser"
    WAERMELESER = "waermeleser"


_PREFIX_MAP: dict[str, DeviceType] = {
    "STROM": DeviceType.STROMLESER,
    "GAS": DeviceType.GASLESER,
    "GAS_PULSE": DeviceType.GASLESER_PULSE,
    "WASSER": DeviceType.WASSERLESER,
    "HEAT": DeviceType.WAERMELESER,
}

# "GAS_PULSE" also starts with "GAS", so the longest match must win.
_PREFIXES_LONGEST_FIRST: tuple[tuple[str, DeviceType], ...] = tuple(
    sorted(_PREFIX_MAP.items(), key=lambda item: len(item[0]), reverse=True)
)

_CUMULATIVE_FIELDS: set[tuple[DeviceType, str]] = {
    (DeviceType.STROMLESER, "1.8.0"),
    (DeviceType.STROMLESER, "1.8.1"),
    (DeviceType.STROMLESER, "1.8.2"),
    (DeviceType.STROMLESER, "1.8.3"),
    (DeviceType.STROMLESER, "1.8.4"),
    (DeviceType.STROMLESER, "2.8.0"),
    (DeviceType.STROMLESER, "2.8.1"),
    (DeviceType.STROMLESER, "2.8.2"),
    (DeviceType.STROMLESER, "2.8.3"),
    (DeviceType.STROMLESER, "2.8.4"),
    (DeviceType.GASLESER, "total_consumption"),
    (DeviceType.GASLESER_PULSE, "total_consumption"),
    (DeviceType.WASSERLESER, "total_consumption"),
    (DeviceType.WAERMELESER, "total_energy_t1"),
    (DeviceType.WAERMELESER, "total_energy_t2"),
    (DeviceType.WAERMELESER, "total_energy_t3"),
    (DeviceType.WAERMELESER, "total_volume"),
}



def detect_device_type(device_id: str) -> DeviceType:
    """Return the DeviceType matching the *device_id* prefix.

    Raises EnergieleserUnknownDeviceError when no prefix matches.
    """
    upper = device_id.upper()
    for prefix, dtype in _PREFIXES_LONGEST_FIRST:
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
    firmware configuration, so every code is treated as optional. Missing,
    non-string, or unparseable values are logged at debug level and treated as
    absent rather than raising.
    """
    raw = payload.get(code)
    if raw is None:
        return None
    if not isinstance(raw, str):
        _LOGGER.debug("Field '%s' expected string, got %s: %s", code, type(raw).__name__, raw)
        return None
    try:
        value, unit = _parse_value_unit(raw)
    except (ValueError, IndexError):
        _LOGGER.debug("Failed to parse field '%s': %s", code, raw)
        return None
    if not unit:
        device_id = payload.get("device_id", "unknown")
        key = (device_id, code)
        if key not in _LOGGED_UNITLESS:
            _LOGGED_UNITLESS.add(key)
            _LOGGER.debug(
                "Device '%s' reported unitless measurement for '%s': %s",
                device_id,
                code,
                value,
            )
    return Measurement(value=value, unit=unit)


def _parse_rssi_dbm(payload: Mapping[str, Any]) -> float | None:
    """Safely extract RSSI dBm value from payload.

    Returns None if rssi field is missing, not a valid number/string, or malformed.
    """
    rssi_raw = payload.get("rssi")
    if rssi_raw is None:
        return None
    if isinstance(rssi_raw, int | float):
        return float(rssi_raw)
    if not isinstance(rssi_raw, str):
        _LOGGER.debug(
            "RSSI expected string or number, got %s: %s", type(rssi_raw).__name__, rssi_raw
        )
        return None
    try:
        value, _ = _parse_value_unit(rssi_raw)
    except (ValueError, IndexError):
        _LOGGER.debug("Failed to parse RSSI: %s", rssi_raw)
        return None
    return value


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
class StromleserOneDevice(EnergieleserDevice):
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
    pin_locked: bool = False

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> StromleserOneDevice:
        """Build a StromleserOneDevice from whatever OBIS codes are present."""
        fields: dict[str, Any] = {}
        for code, attr in _STROMLESER_READINGS.items():
            if (measurement := _measurement(payload, code)) is not None:
                if (
                    measurement.value == 0.0
                    and (DeviceType.STROMLESER, code) in _CUMULATIVE_FIELDS
                ):
                    continue

                fields[attr] = measurement
        # "16.7" is a firmware alias for "16.7.0"; only used as a fallback.
        if "power_active" not in fields and (alias := _measurement(payload, "16.7")):
            fields["power_active"] = alias
        pin_locked = "power_active" not in fields
        return cls(
            device_id=payload["device_id"],
            device_type=DeviceType.STROMLESER,
            timestamp=int(payload["timestamp"]),
            signal_strength_dbm=_parse_rssi_dbm(payload),
            pin_locked=pin_locked,
            **fields,
        )


def _gasleser_fields(payload: Mapping[str, Any], device_type: DeviceType) -> dict[str, Any]:
    """Parse the pulse-counter payload shared by gasleser and gasleser.pulse."""
    count = payload.get("count")
    total = payload.get("total_consumption")
    flow = payload.get("current_flow_rate")

    total_consumption: float | None = None
    if total is not None:
        total_val = float(total)
        if not (
            total_val == 0.0 and (device_type, "total_consumption") in _CUMULATIVE_FIELDS
        ):
            total_consumption = total_val

    return {
        "device_id": payload["device_id"],
        "device_type": device_type,
        "timestamp": int(payload["timestamp"]),
        "count": int(count) if count is not None else None,
        "total_consumption": total_consumption,
        "current_flow_rate": float(flow) if flow is not None else None,
        "signal_strength_dbm": _parse_rssi_dbm(payload),
    }


@dataclass(frozen=True, kw_only=True, slots=True)
class GasleserDevice(EnergieleserDevice):
    """Parsed response for a gasleser (gas meter)."""

    count: int | None = None
    total_consumption: float | None = None
    current_flow_rate: float | None = None
    signal_strength_dbm: float | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> GasleserDevice:
        """Build a GasleserDevice from whatever fields are present."""
        return cls(**_gasleser_fields(payload, DeviceType.GASLESER))


@dataclass(frozen=True, kw_only=True, slots=True)
class GasleserPulseDevice(EnergieleserDevice):
    """Parsed response for a gasleser.pulse (gas meter).

    Reports the same fields as :class:`GasleserDevice`; only the device type
    and the ``GAS_PULSE`` id prefix differ.
    """

    count: int | None = None
    total_consumption: float | None = None
    current_flow_rate: float | None = None
    signal_strength_dbm: float | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> GasleserPulseDevice:
        """Build a GasleserPulseDevice from whatever fields are present."""
        return cls(**_gasleser_fields(payload, DeviceType.GASLESER_PULSE))


_WASSERLESER_FIELDS = (
    "total_consumption",
    "today_consumption",
    "current_flow_rate",
    "current_flow_rate_m3",
)


@dataclass(frozen=True, kw_only=True, slots=True)
class WasserleserDevice(EnergieleserDevice):
    """Parsed response for a wasserleser (water meter)."""

    total_consumption: Measurement | None = None
    today_consumption: Measurement | None = None
    current_flow_rate: Measurement | None = None
    current_flow_rate_m3: Measurement | None = None
    signal_strength_dbm: float | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> WasserleserDevice:
        """Build a WasserleserDevice from whatever fields are present."""
        fields: dict[str, Any] = {}
        for name in _WASSERLESER_FIELDS:
            if (measurement := _measurement(payload, name)) is not None:
                if (
                    measurement.value == 0.0
                    and (DeviceType.WASSERLESER, name) in _CUMULATIVE_FIELDS
                ):
                    continue

                fields[name] = measurement
        signal = _measurement(payload, "signal_strength")
        return cls(
            device_id=payload["device_id"],
            device_type=DeviceType.WASSERLESER,
            timestamp=int(payload["timestamp"]),
            signal_strength_dbm=signal.value if signal is not None else None,
            **fields,
        )


_WAERMELESER_FIELDS = (
    "total_energy_t1",
    "total_energy_t2",
    "total_energy_t3",
    "power",
    "total_volume",
    "volume_flow",
    "flow_temperature",
    "return_temperature",
    "temperature_difference",
)

# Heat meters emit -327.00 °C as a sentinel meaning "no temperature available"
# (sensor disconnected or value not yet measured). Treat such readings as absent.
_WAERMELESER_TEMPERATURE_FIELDS = frozenset(
    {"flow_temperature", "return_temperature"}
)
_WAERMELESER_TEMPERATURE_SENTINEL = -327.0


@dataclass(frozen=True, kw_only=True, slots=True)
class WaermeleserDevice(EnergieleserDevice):
    """Parsed response for a wärmeleser (heat meter)."""

    total_energy_t1: Measurement | None = None
    total_energy_t2: Measurement | None = None
    total_energy_t3: Measurement | None = None
    power: Measurement | None = None
    total_volume: Measurement | None = None
    volume_flow: Measurement | None = None
    flow_temperature: Measurement | None = None
    return_temperature: Measurement | None = None
    temperature_difference: Measurement | None = None
    fabrication_number: str | None = None
    signal_strength_dbm: float | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> WaermeleserDevice:
        """Build a WaermeleserDevice from whatever fields are present."""
        fields: dict[str, Any] = {}
        for name in _WAERMELESER_FIELDS:
            if (measurement := _measurement(payload, name)) is not None:
                if (
                    measurement.value == 0.0
                    and (DeviceType.WAERMELESER, name) in _CUMULATIVE_FIELDS
                ):
                    continue
                if (
                    name in _WAERMELESER_TEMPERATURE_FIELDS
                    and measurement.value == _WAERMELESER_TEMPERATURE_SENTINEL
                ):
                    continue
                fields[name] = measurement
        return cls(
            device_id=payload["device_id"],
            device_type=DeviceType.WAERMELESER,
            timestamp=int(payload["timestamp"]),
            fabrication_number=payload.get("fabrication_number"),
            signal_strength_dbm=_parse_rssi_dbm(payload),
            **fields,
        )


_DEVICE_BUILDERS: dict[DeviceType, Callable[[Mapping[str, Any]], EnergieleserDevice]] = {
    DeviceType.STROMLESER: StromleserOneDevice.from_payload,
    DeviceType.GASLESER: GasleserDevice.from_payload,
    DeviceType.GASLESER_PULSE: GasleserPulseDevice.from_payload,
    DeviceType.WASSERLESER: WasserleserDevice.from_payload,
    DeviceType.WAERMELESER: WaermeleserDevice.from_payload,
}


def parse_device(payload: Mapping[str, Any]) -> EnergieleserDevice:
    """Detect the device type from *payload* and return its typed dataclass."""
    try:
        device_id = payload["device_id"]
    except KeyError as err:
        raise EnergieleserUnknownDeviceError("unknown") from err  # noqa: EM101
    device_type = detect_device_type(device_id)
    return _DEVICE_BUILDERS[device_type](payload)

