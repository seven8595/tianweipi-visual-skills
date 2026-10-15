# run-h3-sample.ps1 - submit one MiniMax H3 I2V sample to a running ComfyUI.
# Prereq: ComfyUI running at http://127.0.0.1:8188
#   E:\ComfyUI_windows_portable\run_nvidia_gpu_fast_fp16_accumulation.bat
#
# Examples:
#   .\run-h3-sample.ps1 -Prompt "a cat walking on neon street" -DurationSec 5
#   .\run-h3-sample.ps1 -Prompt "..." -DryRun        # no network, just print what would submit
#   .\run-h3-sample.ps1 -FirstFrame F:\upscale_work\input.jpg

param(
  [string]$ComfyUiUrl = "http://127.0.0.1:8188",
  [string]$WorkflowPath = "D:\AI_WORKSPACE\h3_template.json",
  [string]$Prompt,
  [double]$DurationSec = 5.0,
  [int]$Seed = -1,
  [string]$OutputPrefix = "sample/sample",
  [string]$FirstFrame = "",
  [switch]$DryRun,
  [int]$TimeoutMin = 30
)

. "$PSScriptRoot\lib.ps1"
$ErrorActionPreference = 'Stop'

# --- 0. Preflight: ComfyUI alive? (skip in DryRun) ---
if (-not $DryRun) {
  try {
    $sys = Invoke-RestMethod -Uri "$ComfyUiUrl/system_stats" -TimeoutSec 3
    Write-Host ("[ok] ComfyUI v{0}, GPU {1}, VRAM free {2:N1} GB" -f $sys.system.comfyui_version, $sys.devices[0].name, ($sys.devices[0].vram_free/1GB)) -ForegroundColor Green
  } catch {
    Write-Host "[fatal] ComfyUI not reachable at $ComfyUiUrl. Start it first:" -ForegroundColor Red
    Write-Host "  E:\ComfyUI_windows_portable\run_nvidia_gpu_fast_fp16_accumulation.bat" -ForegroundColor Yellow
    exit 1
  }
}

if (-not (Test-Path $WorkflowPath)) {
  Write-Host "[fatal] workflow not found: $WorkflowPath" -ForegroundColor Red; exit 1
}

# --- 1. Load workflow ---
$wf = Read-Workflow -Path $WorkflowPath

# --- 2. Apply overrides ---
if ($Prompt) {
  $wf.'105:104'.inputs.prompt = $Prompt
  Write-Host "[cfg] prompt -> $($Prompt.Substring(0,[Math]::Min(80,$Prompt.Length)))..."
}
$wf.'105:111'.inputs.value = $DurationSec
Write-Host "[cfg] duration -> ${DurationSec}s"

if ($Seed -lt 0) { $Seed = Get-Random -Maximum 2147483647 }
$wf.'105:15'.inputs.noise_seed = $Seed
Write-Host "[cfg] seed -> $Seed"

$wf.'92'.inputs.filename_prefix = $OutputPrefix
Write-Host "[cfg] output prefix -> $OutputPrefix"

# --- 3. Upload first frame if requested ---
if ($FirstFrame -and (Test-Path $FirstFrame)) {
  Write-Host "[up] uploading first frame: $FirstFrame"
  $upload = New-MultipartFileBody -FilePath $FirstFrame -FieldName "image"
  $resp = Invoke-RestMethod -Uri "$ComfyUiUrl/upload/image" -Method Post -ContentType $upload.ContentType -Body $upload.Body
  $wf.'114'.inputs.image = $resp.name
  Write-Host "[ok] first frame -> $($resp.name)"
} elseif ($FirstFrame) {
  Write-Host "[warn] FirstFrame not found: $FirstFrame (keeping template default)" -ForegroundColor Yellow
}

# --- 4. Submit (or dry-run) ---
$start = Get-Date
$result = Submit-ComfyWorkflow -ComfyUiUrl $ComfyUiUrl -Workflow $wf -TimeoutMin $TimeoutMin -DryRun:$DryRun
$dur = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)

if (-not $result.ok) {
  Write-Host "[fatal] $($result.error)" -ForegroundColor Red; exit 1
}

if ($result.dryRun) {
  Write-Host "[dry-run] OK in ${dur}s, nothing submitted" -ForegroundColor Yellow
} else {
  Write-Host ""
  Write-Host "===== DONE in ${dur}s =====" -ForegroundColor Green
  Write-Host ("Output under ComfyUI/output/ (prefix: $OutputPrefix)") -ForegroundColor Green
}
