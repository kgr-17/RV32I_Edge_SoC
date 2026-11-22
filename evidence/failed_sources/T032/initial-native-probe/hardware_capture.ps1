param([Parameter(Mandatory=$true)][string]$Job)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$data = Get-Content -LiteralPath $Job -Raw -Encoding UTF8 | ConvertFrom-Json
& $data.python -B (Join-Path $PSScriptRoot 'hardware.py') guard --capture-job $Job
if ($LASTEXITCODE -ne 0) { throw 'HARDWARE_CAPTURE_GUARD' }
$serial = New-Object System.IO.Ports.SerialPort($data.com,115200,[System.IO.Ports.Parity]::None,8,[System.IO.Ports.StopBits]::One)
$serial.Handshake = [System.IO.Ports.Handshake]::None
$serial.DtrEnable = $false
$serial.RtsEnable = $false
$serial.ReadTimeout = 100
$serial.WriteTimeout = 100
$raw = $null
$events = $null
$subscription = $null
$eventName = 'T032-' + [Guid]::NewGuid().ToString('N')
try {
    $raw = [IO.File]::Open((Join-Path $data.output 'uart.bin'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    $events = New-Object IO.StreamWriter((Join-Path $data.output 'events.jsonl'),$false,(New-Object Text.UTF8Encoding($false)))
    $subscription = Register-ObjectEvent -InputObject $serial -EventName ErrorReceived -SourceIdentifier $eventName
    $serial.Open()
    Write-Output ('HARDWARE_UART_READY ' + $data.com)
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $buffer = New-Object byte[] 256
    while ($clock.Elapsed.TotalSeconds -lt $data.seconds) {
        try {
            $count = $serial.Read($buffer,0,$buffer.Length)
            if ($count -gt 0) {
                $raw.Write($buffer,0,$count); $raw.Flush()
                $events.WriteLine((@{elapsed_ms=$clock.Elapsed.TotalMilliseconds; utc=[DateTime]::UtcNow.ToString('o'); hex=([BitConverter]::ToString($buffer,0,$count)).Replace('-','').ToLowerInvariant()} | ConvertTo-Json -Compress)); $events.Flush()
            }
        } catch [TimeoutException] { }
    }
    $errors = @(Get-Event -SourceIdentifier $eventName -ErrorAction SilentlyContinue)
    foreach ($event in $errors) {
        $events.WriteLine((@{serial_error=[string]$event.SourceEventArgs.EventType; utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress))
    }
    if ($errors.Count -ne 0) {throw 'HARDWARE_UART_SERIAL_ERROR'}
    Write-Output 'HARDWARE_UART_CAPTURE_COMPLETE'
} finally {
    if ($serial.IsOpen) {$serial.Close()}
    $serial.Dispose()
    if ($null -ne $raw) {$raw.Dispose()}
    if ($null -ne $events) {$events.Dispose()}
    if ($null -ne $subscription) {Unregister-Event -SourceIdentifier $eventName}
    Get-Event -SourceIdentifier $eventName -ErrorAction SilentlyContinue | Remove-Event -ErrorAction SilentlyContinue
}
