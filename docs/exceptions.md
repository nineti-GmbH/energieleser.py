# Exceptions

```
EnergieleserError
├── EnergieleserConnectionError
│   └── EnergieleserTimeoutError
└── EnergieleserUnknownDeviceError
```

Catch `EnergieleserConnectionError` to handle both network failures and request timeouts.

`EnergieleserUnknownDeviceError` is raised when a `device_id` prefix does not match any of the supported device families.
