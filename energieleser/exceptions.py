"""Exception types raised by the energieleser client."""

from __future__ import annotations


class EnergieleserError(Exception):
    """Base exception for the energieleser client."""


class EnergieleserConnectionError(EnergieleserError):
    """Raised when the device cannot be reached."""


class EnergieleserTimeoutError(EnergieleserConnectionError):
    """Raised when a request to the device times out."""


class EnergieleserUnknownDeviceError(EnergieleserError):
    """Raised when a device_id prefix does not match any known device type."""

    def __init__(self, device_id: str) -> None:
        """Store *device_id* and build a human-readable message."""
        super().__init__(f"Unknown device id prefix: {device_id}")
        self.device_id = device_id
