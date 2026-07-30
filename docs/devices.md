# Supported devices

| Device         | `device_id` prefix | Dataclass              |
| -------------- | ------------------ | ---------------------- |
| stromleser     | `STROM`            | `StromleserOneDevice`  |
| gasleser       | `GAS`              | `GasleserDevice`       |
| gasleser.pulse | `GAS_PULSE`        | `GasleserPulseDevice`  |
| wasserleser    | `WASSER`           | `WasserleserDevice`    |
| wärmeleser     | `HEAT`             | `WaermeleserDevice`    |

Prefixes are matched longest-first, so a `GAS_PULSE_…` id resolves to `GasleserPulseDevice` rather than the plain `GasleserDevice`.

`GasleserPulseDevice` carries the same fields as `GasleserDevice` — `count`, `total_consumption`, `current_flow_rate` and `signal_strength_dbm` — and parses an identical payload; the two are distinguished only by `device_id` prefix and `device_type`. Both report consumption and flow as bare floats (no unit is sent), and both take `signal_strength_dbm` from the payload's `rssi` field, since `signal_strength` on these devices is a percentage.

`WaermeleserDevice` currently exposes the raw response under `.raw`; typed fields will be added once its API contract is finalised.

Each typed device exposes its readings as `Measurement(value: float, unit: str)` (e.g. `device.power_active.value`, `device.power_active.unit`). Fields not reported by the meter are `None`.
