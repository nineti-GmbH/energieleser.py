"""Async Python client for energieleser devices."""

import logging
from importlib.metadata import PackageNotFoundError, version

from energieleser.client import EnergieleserClient
from energieleser.exceptions import (
    EnergieleserConnectionError,
    EnergieleserError,
    EnergieleserTimeoutError,
    EnergieleserUnknownDeviceError,
)
from energieleser.models import (
    DeviceType,
    EnergieleserDevice,
    GasleserDevice,
    Measurement,
    StromleserOneDevice,
    WaermeleserDevice,
    WasserleserDevice,
    detect_device_type,
    parse_device,
)

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    # Running from a source tree without an installed distribution.
    __version__ = "0.0.0"

__all__ = [
    "DeviceType",
    "EnergieleserClient",
    "EnergieleserConnectionError",
    "EnergieleserDevice",
    "EnergieleserError",
    "EnergieleserTimeoutError",
    "EnergieleserUnknownDeviceError",
    "GasleserDevice",
    "Measurement",
    "StromleserOneDevice",
    "WaermeleserDevice",
    "WasserleserDevice",
    "detect_device_type",
    "parse_device",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
