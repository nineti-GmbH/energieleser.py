"""Tests for ``detect_device_type``."""

from __future__ import annotations

import pytest

from energieleser import DeviceType, detect_device_type
from energieleser.exceptions import EnergieleserUnknownDeviceError


@pytest.mark.parametrize(
    ("device_id", "expected"),
    [
        ("STROM_ONE_8529546829", DeviceType.STROMLESER),
        ("strom_one_lowercase", DeviceType.STROMLESER),
        ("GAS_8530321017", DeviceType.GASLESER),
        ("WASSER_0000000001", DeviceType.WASSERLESER),
        ("HEAT_0000000001", DeviceType.WAERMELESER),
    ],
)
def test_detect_known_prefixes(device_id: str, expected: DeviceType) -> None:
    assert detect_device_type(device_id) is expected


def test_detect_unknown_prefix_raises() -> None:
    with pytest.raises(EnergieleserUnknownDeviceError) as excinfo:
        detect_device_type("FOO_123")
    assert excinfo.value.device_id == "FOO_123"
