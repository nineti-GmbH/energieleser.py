# Supported devices

| Device      | `device_id` prefix | Dataclass           |
| ----------- | ------------------ | ------------------- |
| stromleser  | `STROM`            | `StromleserOneDevice`  |
| gasleser    | `GAS`              | `GasleserDevice`    |
| wasserleser | `WASSER`           | `WasserleserDevice` |
| wärmeleser  | `HEAT`             | `WaermeleserDevice` |

`WaermeleserDevice` currently exposes the raw response under `.raw`; typed fields will be added once its API contract is finalised.

Each typed device exposes its readings as `Measurement(value: float, unit: str)` (e.g. `device.power_active.value`, `device.power_active.unit`). Fields not reported by the meter are `None`.
