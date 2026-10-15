# watch-vram.ps1 - sample GPU VRAM / util / temp and free RAM every N seconds.
# Press Ctrl+C to stop; prints peak and average at exit.
# Read-only, does not touch any process.

param(
  [int]$IntervalSec = 2
)

$ErrorActionPreference = 'SilentlyContinue'

$peakVramMiB = 0
$lowestFreeRamGB = [double]::MaxValue
$peakUsedRamGB = 0
$peakTempC = 0
$samples = 0
$vramSum = 0
$utilSum = 0
$totalRAMGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB, 1)

Write-Host "Sampling every ${IntervalSec}s. Press Ctrl+C to stop and see summary." -ForegroundColor Cyan
Write-Host ("{0,-10} {1,-14} {2,-10} {3,-8} {4,-12}" -f "time", "vramUsed", "gpuUtil", "temp", "freeRAM(GB)")

try {
  while ($true) {
    $gpu = nvidia-smi --query-gpu=memory.used,utilization.gpu,temperature.gpu --format=csv,noheader,nounits 2>$null
    if ($gpu) {
      $parts = $gpu -split ',' | ForEach-Object { $_.Trim() }
      $vram = [int]$parts[0]
      $util = [int]$parts[1]
      $temp = [int]$parts[2]

      $os = Get-CimInstance Win32_OperatingSystem
      $freeRamGB = [math]::Round($os.FreePhysicalMemory/1MB, 1)
      $usedRamGB = [math]::Round($totalRAMGB - $freeRamGB, 1)

      $now = Get-Date -Format "HH:mm:ss"
      Write-Host ("{0,-10} {1,6} MiB {2,7}% {3,6} C {4,10}" -f $now, $vram, $util, $temp, $freeRamGB)

      if ($vram -gt $peakVramMiB) { $peakVramMiB = $vram }
      if ($freeRamGB -lt $lowestFreeRamGB) { $lowestFreeRamGB = $freeRamGB }
      if ($usedRamGB -gt $peakUsedRamGB) { $peakUsedRamGB = $usedRamGB }
      if ($temp -gt $peakTempC) { $peakTempC = $temp }
      $vramSum += $vram
      $utilSum += $util
      $samples++
    }
    Start-Sleep -Seconds $IntervalSec
  }
}
finally {
  Write-Host "`n===== SUMMARY =====" -ForegroundColor Yellow
  Write-Host ("Samples            : {0}" -f $samples)
  if ($samples -gt 0) {
    Write-Host ("Peak VRAM used     : {0} MiB (of 16303 MiB)" -f $peakVramMiB)
    Write-Host ("Avg VRAM used      : {0} MiB" -f [math]::Round($vramSum/$samples,0))
    Write-Host ("Avg GPU util       : {0} %" -f [math]::Round($utilSum/$samples,1))
  }
  Write-Host ("Peak GPU temp      : {0} C" -f $peakTempC)
  Write-Host ("Lowest free RAM    : {0} GB (of {1} GB)" -f $lowestFreeRamGB, $totalRAMGB)
  Write-Host ("Peak used RAM      : {0} GB" -f $peakUsedRamGB)
  Write-Host ""
  if ($peakVramMiB -gt 15500) {
    Write-Host "WARNING: peak VRAM > 15.5 GB, next similar run will likely OOM." -ForegroundColor Red
  }
  if ($lowestFreeRamGB -lt 4) {
    Write-Host "WARNING: free RAM dropped below 4 GB, system was swapping. Close apps next time." -ForegroundColor Red
  }
}
