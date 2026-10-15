# run-h3-batch.ps1 - batch submit MiniMax H3 I2V jobs from a prompts.txt
# Each line = one video. Blank lines and lines starting with # are ignored.
#
# Usage:
#   .\run-h3-batch.ps1 -PromptsFile D:\AI_WORKSPACE\prompts.txt -DurationSec 5
#   .\run-h3-batch.ps1 -PromptsFile prompts.txt -DryRun     # no ComfyUI needed, verify parsing + CSV
# Output: batch_<timestamp>.csv next to prompts.txt.

param(
  [Parameter(Mandatory=$true)][string]$PromptsFile,
  [string]$ComfyUiUrl = "http://127.0.0.1:8188",
  [string]$WorkflowPath = "D:\AI_WORKSPACE\h3_template.json",
  [double]$DurationSec = 5.0,
  [string]$FirstFrame = "",
  [string]$OutputPrefixBase = "batch",
  [int]$MaxRetries = 1,
  [int]$TimeoutMinPerJob = 20,
  [switch]$DryRun
)

. "$PSScriptRoot\lib.ps1"
$ErrorActionPreference = 'Stop'

# --- preflight ---
if (-not $DryRun) {
  try {
    $sys = Invoke-RestMethod -Uri "$ComfyUiUrl/system_stats" -TimeoutSec 3
    Write-Host ("[ok] ComfyUI v{0}, VRAM free {1:N1} GB" -f $sys.system.comfyui_version, ($sys.devices[0].vram_free/1GB)) -ForegroundColor Green
  } catch {
    Write-Host "[fatal] ComfyUI not reachable at $ComfyUiUrl" -ForegroundColor Red; exit 1
  }
} else {
  Write-Host "[dry-run] skipping ComfyUI preflight" -ForegroundColor Yellow
}
if (-not (Test-Path $PromptsFile)) { Write-Host "[fatal] prompts file not found: $PromptsFile" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $WorkflowPath)) { Write-Host "[fatal] workflow not found: $WorkflowPath" -ForegroundColor Red; exit 1 }

$lines = Get-Content $PromptsFile -Encoding UTF8 | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" -and -not $_.StartsWith("#") }
if ($lines.Count -eq 0) { Write-Host "[fatal] no prompts in $PromptsFile" -ForegroundColor Red; exit 1 }
Write-Host ("[ok] {0} prompts queued" -f $lines.Count) -ForegroundColor Cyan

# upload first frame once
$firstFrameName = ""
if ($FirstFrame -and (Test-Path $FirstFrame) -and -not $DryRun) {
  $upload = New-MultipartFileBody -FilePath $FirstFrame -FieldName "image"
  $resp = Invoke-RestMethod -Uri "$ComfyUiUrl/upload/image" -Method Post -ContentType $upload.ContentType -Body $upload.Body
  $firstFrameName = $resp.name
  Write-Host "[ok] first frame -> $firstFrameName"
} elseif ($FirstFrame -and $DryRun) {
  Write-Host "[dry-run] would upload first frame: $FirstFrame" -ForegroundColor DarkGray
}

$results = @()
$batchTag = Get-Date -Format "yyyyMMdd_HHmmss"
$totalStart = Get-Date

for ($i = 0; $i -lt $lines.Count; $i++) {
  $promptText = $lines[$i]
  $idx = $i + 1
  $prefix = "$OutputPrefixBase/${batchTag}/$('{0:d3}' -f $idx)"
  $seed = Get-Random -Maximum 2147483647

  $ok = $false; $attempt = 0; $jobStart = Get-Date; $finalError = ""
  while (-not $ok -and $attempt -le $MaxRetries) {
    $attempt++
    Write-Host ""
    Write-Host ("[{0}/{1}] attempt {2} | seed={3}" -f $idx, $lines.Count, $attempt, $seed) -ForegroundColor Cyan
    Write-Host ("  prompt: " + $promptText.Substring(0,[Math]::Min(90,$promptText.Length)))

    # re-read template each job (cheapest reliable deep copy in PS5.1)
    $wf = Read-Workflow -Path $WorkflowPath
    $wf.'105:104'.inputs.prompt = $promptText
    $wf.'105:111'.inputs.value = $DurationSec
    $wf.'105:15'.inputs.noise_seed = $seed
    $wf.'92'.inputs.filename_prefix = $prefix
    if ($firstFrameName) { $wf.'114'.inputs.image = $firstFrameName }

    $r = Submit-ComfyWorkflow -ComfyUiUrl $ComfyUiUrl -Workflow $wf -TimeoutMin $TimeoutMinPerJob -DryRun:$DryRun
    if ($r.ok) { $ok = $true; break }
    $finalError = $r.error
    Write-Host ("  [retry] " + $finalError) -ForegroundColor Yellow
    Start-Sleep -Seconds 3
  }

  $jobDur = [math]::Round(((Get-Date) - $jobStart).TotalSeconds, 1)
  $status = if ($ok) { "OK" } else { "FAIL" }
  Write-Host ("  -> {0} in {1}s" -f $status, $jobDur) -ForegroundColor $(if($ok){'Green'}else{'Red'})

  $results += [pscustomobject]@{
    index = $idx; prompt = $promptText; seed = $seed
    duration_sec = $DurationSec; output_prefix = $prefix
    status = $status; job_seconds = $jobDur
    attempts = $attempt; error = $finalError
  }
}

$totalDur = [math]::Round(((Get-Date) - $totalStart).TotalMinutes, 1)
$csvPath = Join-Path (Split-Path $PromptsFile -Parent) "batch_${batchTag}.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "===== BATCH DONE in ${totalDur} min =====" -ForegroundColor Green
$results | Format-Table index,status,job_seconds,seed -AutoSize
Write-Host ("Summary CSV: " + $csvPath) -ForegroundColor Cyan
$okCount = ($results | Where-Object status -eq 'OK').Count
$failCount = ($results | Where-Object status -eq 'FAIL').Count
Write-Host ("Success: {0}/{1} | Failed: {2}/{1}" -f $okCount, $results.Count, $failCount)
