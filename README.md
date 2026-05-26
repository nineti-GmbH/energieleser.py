# energieleser.py

[![PyPI](https://img.shields.io/pypi/v/energieleser.svg)](https://pypi.org/project/energieleser/)
[![Python](https://img.shields.io/pypi/pyversions/energieleser.svg)](https://pypi.org/project/energieleser/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Async Python client for energieleser smart meter devices.

Talks to the device's local HTTP API and returns typed dataclasses for **stromleser.one**, **gasleser**, **wasserleser** and **wärmeleser**. Powers the upcoming Home Assistant integration.

## Installing / Getting started

```shell
pip install energieleser
```

```python
import asyncio
from energieleser import EnergieleserClient

async def main() -> None:
    async with EnergieleserClient("192.168.1.100") as client:
        device = await client.get_device()
        print(device.device_id, device.device_type)

asyncio.run(main())
```

More examples in [docs/usage.md](docs/usage.md).

## Features

- Async HTTP client built on `aiohttp`.
- Typed, frozen, slotted dataclasses per device family.
- Automatic device-type detection from `device_id` prefix.
- Optional `Measurement(value, unit)` fields — missing readings stay `None` instead of raising.
- Bring-your-own `aiohttp.ClientSession`, or let the client manage one.
- Structured exception hierarchy for clean error handling.

## Configuration

`EnergieleserClient(host, port=80, *, session=None, request_timeout=10.0)`

| Argument          | Type                          | Default | Description                                                                |
| ----------------- | ----------------------------- | ------- | -------------------------------------------------------------------------- |
| `host`            | `str`                         | —       | Device IP address or hostname.                                             |
| `port`            | `int`                         | `80`    | Device HTTP port.                                                          |
| `session`         | `aiohttp.ClientSession\|None` | `None`  | Reuse an existing session. If `None`, the client creates and owns its own. |
| `request_timeout` | `float`                       | `10.0`  | Per-request timeout in seconds.                                            |

## Documentation

- [Usage](docs/usage.md) — examples, shared sessions
- [Supported devices](docs/devices.md) — device families, fields
- [Exceptions](docs/exceptions.md) — exception hierarchy
- [Development](docs/development.md) — local setup, lint, tests
- [Publishing](docs/publishing.md) — release workflow
- [Contributing](docs/contributing.md) — how to contribute

## Links

- PyPI: https://pypi.org/project/energieleser/
- Repository: https://github.com/nineti-GmbH/energieleser.py
- Issue tracker: https://github.com/nineti-GmbH/energieleser.py/issues
- Homepage: https://energieleser.de

## Licensing

The code in this project is licensed under the MIT license — see [LICENSE](LICENSE).

© [nineti GmbH](https://energieleser.de)
