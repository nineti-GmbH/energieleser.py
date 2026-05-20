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
