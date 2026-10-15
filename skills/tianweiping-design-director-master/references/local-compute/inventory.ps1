# local-compute-scheduler: read-only resource inventory
# Safe to run anytime. Does not modify anything.

$ErrorActionPreference = 'SilentlyContinue'
Write-Host "===== CPU / RAM =====" -ForegroundColor Cyan
$cs = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor
$os = Get-CimInstance Win32_OperatingSystem
$totalRAM = [math]::Round($cs.TotalPhysicalMemory/1GB,1)
# Win32_OperatingSystem.FreePhysicalMemory is in KB; 1 GB = 1048576 KB
$freeRAM  = [math]::Round($os.FreePhysicalMemory/1MB,1)
$usedRAM  = [math]::Round($totalRAM - $freeRAM,1)
Write-Host ("CPU : {0} ({1}C/{2}T)" -f $cpu.Name, $cpu.NumberOfCores, $cpu.NumberOfLogicalProcessors)
Write-Host ("RAM : {0} GB total | {1} GB used | {2} GB free" -f $totalRAM, $usedRAM, $freeRAM)

Write-Host "`n===== GPU =====" -ForegroundColor Cyan
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu,power.draw,driver_version --format=csv,noheader

Write-Host "`n===== GPU compute processes (real VRAM hogs) =====" -ForegroundColor Cyan
$computeApps = nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>$null
if ($computeApps -and $computeApps.Trim().Length -gt 0) {
  $computeApps
} else {
  Write-Host "(nvidia-smi couldn't list compute apps - RTX 50 permission quirk)"
  Write-Host "Likely GPU users right now:"
  Get-Process | Where-Object { $_.Path -match "python|ComfyUI|ollama|chrome|msedge|firefox" } |
    Select-Object @{n='Name';e={$_.Name}}, Id, @{n='MemMB';e={[math]::Round($_.WorkingSet64/1MB,0)}}, Path |
    Format-Table -AutoSize | Out-String | Write-Host
}

Write-Host "`n===== Disks =====" -ForegroundColor Cyan
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
  $sizeGB = [math]::Round($_.Size/1GB,1)
  $freeGB = [math]::Round($_.FreeSpace/1GB,1)
  $pct = [math]::Round(($_.Size-$_.FreeSpace)/$_.Size*100,1)
  Write-Host ("{0}  {1,7} GB total  {2,7} GB free  ({3}% used)" -f $_.DeviceID, $sizeGB, $freeGB, $pct)
}

Write-Host "`n===== Top 10 RAM hogs =====" -ForegroundColor Cyan
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 |
  ForEach-Object { "{0,-30} {1,8} MB" -f $_.Name, [math]::Round($_.WorkingSet64/1MB,0) }

Write-Host "`n===== LAN neighbors (are Mac/iPhone/iPad reachable?) =====" -ForegroundColor Cyan
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*'} |
  ForEach-Object { "iface {0,-15} {1}/{2}" -f $_.InterfaceAlias, $_.IPAddress, $_.PrefixLength }
Get-NetNeighbor -AddressFamily IPv4 | Where-Object {
  $_.IPAddress -notlike '224.*' -and $_.IPAddress -notlike '230.*' -and
  $_.IPAddress -notlike '255.*' -and $_.State -ne 'Unreachable'
} | Sort-Object IPAddress | ForEach-Object { "  {0,-15} {1}  [{2}]" -f $_.IPAddress, $_.LinkLayerAddress, $_.State }

Write-Host "`n===== Runtime stack =====" -ForegroundColor Cyan
Write-Host ("Ollama : " + ((ollama --version 2>&1) -join ' '))
$comfyPy = "E:\ComfyUI_windows_portable\python_embeded\python.exe"
if (Test-Path $comfyPy) {
  $torch = & $comfyPy -c "import torch; print(f'torch={torch.__version__} cuda={torch.cuda.is_available()} cc={torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None}')" 2>&1
  Write-Host ("ComfyUI embedded python: " + $torch)
} else {
  Write-Host "ComfyUI embedded python NOT found at expected path"
}
Write-Host ("ffmpeg : " + ((ffmpeg -version 2>&1 | Select-Object -First 1) -replace 'ffmpeg version ',''))

Write-Host "`n===== Ollama models loaded right now =====" -ForegroundColor Cyan
try {
  $ps = Invoke-RestMethod -Uri http://localhost:11434/api/ps -TimeoutSec 2
  if ($ps.models -and $ps.models.Count -gt 0) { $ps.models | Format-Table name,size_vram,expires_at -AutoSize }
  else { Write-Host "(no model loaded in VRAM right now)" }
} catch {
  Write-Host "REST API not on :11434, trying 'ollama ps':"
  ollama ps 2>&1
}

# ===== GO / NO-GO for MiniMax H3 video generation =====
Write-Host "`n===== GO / NO-GO: can we run H3 now? =====" -ForegroundColor Cyan

# check ComfyUI
$comfyUp = $false
try { $null = Invoke-RestMethod -Uri "http://127.0.0.1:8188/system_stats" -TimeoutSec 2; $comfyUp = $true } catch { }

# check free VRAM from nvidia-smi
$gpuLine = (nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>$null)
$freeVramGB = [math]::Round([int]($gpuLine -split ',')[0] / 1024, 1)

$go = $true
Write-Host ""
if ($freeRAM -lt 20) {
  Write-Host ("[NO-GO] free RAM {0} GB < 20 GB needed for H3 offload" -f $freeRAM) -ForegroundColor Red
  Write-Host "        -> close Chrome extra tabs / ChatGPT / Coze / Steam / EA / douyin" -ForegroundColor Yellow
  $go = $false
} else {
  Write-Host ("[OK] free RAM {0} GB >= 20 GB" -f $freeRAM) -ForegroundColor Green
}

if ($freeVramGB -lt 12) {
  Write-Host ("[NO-GO] free VRAM {0} GB < 12 GB needed" -f $freeVramGB) -ForegroundColor Red
  $go = $false
} else {
  Write-Host ("[OK] free VRAM {0} GB >= 12 GB" -f $freeVramGB) -ForegroundColor Green
}

if (-not $comfyUp) {
  Write-Host "[NO-GO] ComfyUI not on :8188" -ForegroundColor Red
  Write-Host "        -> start: E:\ComfyUI_windows_portable\run_nvidia_gpu_fast_fp16_accumulation.bat" -ForegroundColor Yellow
  $go = $false
} else {
  Write-Host "[OK] ComfyUI alive on :8188" -ForegroundColor Green
}

Write-Host ""
if ($go) {
  Write-Host ">>> READY: run-h3-sample.ps1 will work. Recommended next command:" -ForegroundColor Green
  Write-Host "    .\run-h3-sample.ps1 -Prompt `"your prompt`" -DurationSec 5" -ForegroundColor Green
} else {
  Write-Host ">>> NOT READY: fix the [NO-GO] items above first. Do NOT start a batch job." -ForegroundColor Red
}

