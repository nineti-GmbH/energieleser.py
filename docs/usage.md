# Usage

```python
import asyncio

from energieleser import EnergieleserClient, StromleserOneDevice


async def main() -> None:
    async with EnergieleserClient("192.168.1.100") as client:
        device = await client.get_device()
        print(device.device_id, device.device_type)
        if isinstance(device, StromleserOneDevice) and device.power_active:
            print(f"Power active: {device.power_active.value} {device.power_active.unit}")


asyncio.run(main())
```

## Sharing an existing `aiohttp.ClientSession`

```python
import aiohttp
from energieleser import EnergieleserClient

async with aiohttp.ClientSession() as session:
    client = EnergieleserClient("192.168.1.100", session=session)
    device = await client.get_device()
    # session is NOT closed by the client when you supply your own
```

## Checking for firmware updates

The OTA server publishes one latest version per device type. The call is
stateless — poll it at whatever cadence suits you (Home Assistant uses 6h).

```python
import aiohttp
from energieleser import get_latest_firmware_versions, is_newer_version

async with aiohttp.ClientSession() as session:
    latest = await get_latest_firmware_versions(session)

installed = "v1.4.22"  # e.g. from the device's mDNS "version" TXT record
if (version := latest.get(device.device_type)) and is_newer_version(installed, version):
    print(f"Firmware {version} available — update via the energieleser app")
```
