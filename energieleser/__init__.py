"""Async Python client for energieleser devices."""

import logging
from importlib.metadata import PackageNotFoundError, version

from energieleser.client import EnergieleserClient
from energieleser.exceptions import (
    EnergieleserConnectionError,
    EnergieleserError,
    EnergieleserParsingError,
    EnergieleserTimeoutError,
    EnergieleserUnknownDeviceError,
)
from energieleser.models import (
    DeviceType,
    EnergieleserDevice,
    GasleserDevice,
    GasleserPulseDevice,
    Measurement,
    StromleserOneDevice,
    WaermeleserDevice,
    WasserleserDevice,
    detect_device_type,
    parse_device,
)
from energieleser.update import (
    LATEST_VERSIONS_URL,
    get_latest_firmware_versions,
    is_newer_version,
)

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    # Running from a source tree without an installed distribution.
    __version__ = "0.0.0"

__all__ = [
    "LATEST_VERSIONS_URL",
    "DeviceType",
    "EnergieleserClient",
    "EnergieleserConnectionError",
    "EnergieleserDevice",
    "EnergieleserError",
    "EnergieleserParsingError",
    "EnergieleserTimeoutError",
    "EnergieleserUnknownDeviceError",
    "GasleserDevice",
    "GasleserPulseDevice",
    "Measurement",
    "StromleserOneDevice",
    "WaermeleserDevice",
    "WasserleserDevice",
    "detect_device_type",
    "get_latest_firmware_versions",
    "is_newer_version",
    "parse_device",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
