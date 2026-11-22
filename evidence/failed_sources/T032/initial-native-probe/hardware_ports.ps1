$ErrorActionPreference = 'Stop'
$ports = @(Get-CimInstance Win32_SerialPort | Where-Object { $_.PNPDeviceID -match 'VID_0403' } |
    Select-Object DeviceID, Name, PNPDeviceID)
$devices = @(Get-PnpDevice -PresentOnly | Where-Object {
    $_.InstanceId -match '^(USB\\VID_0403|FTDIBUS\\)' } |
    Select-Object Status, Class, FriendlyName, InstanceId)
@{serial_ports=$ports; ftdi_devices=$devices} | ConvertTo-Json -Depth 5 -Compress
