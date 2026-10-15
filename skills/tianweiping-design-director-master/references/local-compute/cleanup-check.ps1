# cleanup-check.ps1 - post-task cleanup audit. Read-only, reports leftovers; deletes NOTHING.
# Run after a batch / long generation job finishes to find what's still holding VRAM/disk.

$ErrorActionPreference = 'SilentlyContinue'
Write-Host "===== POST-TASK CLEANUP AUDIT =====" -ForegroundColor Cyan
Write-Host ("time: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Write-Host ""

# 1. VRAM still held?
Write-Host "--- 1. VRAM still held by GPU processes ---" -ForegroundColor Yellow
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
Write-Host ""
Write-Host "Processes attached to GPU:"
$procs = nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>$null
if ($procs) { $procs | ForEach-Object { Write-Host "  $_" } } else { Write-Host "  (none - GPU clean)" }

# 2. ComfyUI / ollama still running?
Write-Host "`n--- 2. Long-running AI processes ---" -ForegroundColor Yellow
$aiProcs = Get-Process | Where-Object {
  $_.Name -match 'python|ollama|comfy' -or
  $_.Path -like "*ComfyUI*python*"
} | Select-Object Name, Id, @{n='MemMB';e={[math]::Round($_.WorkingSet64/1MB,0)}}, Path
if ($aiProcs) { $aiProcs | Format-Table -AutoSize } else { Write-Host "  (none)" }

# 3. Ollama models still loaded in VRAM
Write-Host "--- 3. Ollama models still in VRAM ---" -ForegroundColor Yellow
try {
  $ps = Invoke-RestMethod -Uri http://localhost:11434/api/ps -TimeoutSec 2
  if ($ps.models -and $ps.models.Count -gt 0) {
    $ps.models | Format-Table name, size_vram, expires_at -AutoSize
    Write-Host "  -> run: ollama stop <name>  to release VRAM now" -ForegroundColor Yellow
  } else {
    Write-Host "  (no model loaded - clean)"
  }
} catch { Write-Host "  (ollama not responding)" }

# 4. ComfyUI output folder size
Write-Host "--- 4. Output disk usage ---" -ForegroundColor Yellow
$outDirs = @(
  "E:\ComfyUI_windows_portable\ComfyUI\output",
  "D:\AI_WORKSPACE\output",
  "F:\"
)
foreach ($d in $outDirs) {
  if (Test-Path $d) {
    $size = (Get-ChildItem $d -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1GB
    $recent = Get-ChildItem $d -Recurse -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Write-Host ("  {0,-50} {1,8:N2} GB   latest: {2}" -f $d, $size, $(if($recent){$recent.LastWriteTime.ToString('MM-dd HH:mm')}else{'(empty)'}))
  }
}

# 5. Free disk right now
Write-Host "`n--- 5. Free disk now ---" -ForegroundColor Yellow
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
  Write-Host ("  {0}  free {1,7:N1} GB / {2,7:N1} GB" -f $_.DeviceID, ($_.FreeSpace/1GB), ($_.Size/1GB))
}

# 6. Free RAM now
Write-Host "`n--- 6. Free RAM now ---" -ForegroundColor Yellow
$os = Get-CimInstance Win32_OperatingSystem
$freeGB = [math]::Round($os.FreePhysicalMemory/1MB,1)
Write-Host ("  free RAM: {0} GB" -f $freeGB)

Write-Host "`n===== REMINDERS =====" -ForegroundColor Cyan
Write-Host "  [ ] ComfyUI window closed? (Ctrl+C in its terminal, not just X)"
Write-Host "  [ ] Ollama stopped models?        ollama list ; ollama stop <name>"
Write-Host "  [ ] Outputs copied off E: drive? (E: only has ~219 GB free)"
Write-Host "  [ ] Batch CSV reviewed?           (next to prompts.txt)"
Write-Host "  [ ] If cloud instance was used: SSH in and power it OFF, delete data disk + EIP"
Write-Host "  [ ] Add actual timing to SKILL.md section 9 baseline table"
