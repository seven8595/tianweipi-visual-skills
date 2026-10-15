# lib.ps1 - shared helpers, Windows PowerShell 5.1 compatible.
# Dot-source this at the top of other scripts:
#   . "$PSScriptRoot\lib.ps1"
#
# Convention: ComfyUI workflow JSON has node ids like "105:104" (with colons).
# In PS 5.1, ConvertFrom-Json returns PSCustomObject; access colon-named nodes
# with $wf.'105:104'  (NOT $wf["105:104"] which is hashtable-only syntax).

function Read-Workflow {
  param([Parameter(Mandatory=$true)][string]$Path)
  $raw = Get-Content $Path -Raw -Encoding UTF8
  return ConvertFrom-Json -InputObject $raw
}

# Build a multipart/form-data body for one file upload.
function New-MultipartFileBody {
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [Parameter(Mandatory=$true)][string]$FieldName,
    [string]$Boundary = ([System.Guid]::NewGuid().ToString())
  )
  $fileBytes = [System.IO.File]::ReadAllBytes($FilePath)
  $fileName = Split-Path $FilePath -Leaf
  $enc = [System.Text.Encoding]::UTF8
  $headText = "--$Boundary`r`nContent-Disposition: form-data; name=`"$FieldName`"; filename=`"$fileName`"`r`nContent-Type: application/octet-stream`r`n`r`n"
  $footText = "`r`n--$Boundary--`r`n"
  $head = $enc.GetBytes($headText)
  $foot = $enc.GetBytes($footText)
  $body = New-Object byte[] ($head.Length + $fileBytes.Length + $foot.Length)
  [Array]::Copy($head,0,$body,0,$head.Length)
  [Array]::Copy($fileBytes,0,$body,$head.Length,$fileBytes.Length)
  [Array]::Copy($foot,0,$body,$head.Length+$fileBytes.Length,$foot.Length)
  return @{ Body = $body; ContentType = "multipart/form-data; boundary=$Boundary" }
}

# Submit a workflow to ComfyUI and poll until done.
# Returns @{ ok; error; history; dryRun }
function Submit-ComfyWorkflow {
  param(
    [Parameter(Mandatory=$true)][string]$ComfyUiUrl,
    [Parameter(Mandatory=$true)]$Workflow,
    [int]$TimeoutMin = 20,
    [int]$PollSec = 5,
    [switch]$DryRun
  )
  $clientId = [System.Guid]::NewGuid().ToString()
  $payload = @{ prompt = $Workflow; client_id = $clientId } | ConvertTo-Json -Depth 30 -Compress

  if ($DryRun) {
    Write-Host "[dry-run] not POSTing. Workflow summary:"
    $p = $Workflow.'105:104'.inputs.prompt
    Write-Host ("  prompt  = " + $p.Substring(0,[Math]::Min(80,$p.Length)))
    Write-Host ("  duration= " + $Workflow.'105:111'.inputs.value)
    Write-Host ("  seed    = " + $Workflow.'105:15'.inputs.noise_seed)
    Write-Host ("  prefix  = " + $Workflow.'92'.inputs.filename_prefix)
    Write-Host ("  first   = " + $Workflow.'114'.inputs.image)
    return @{ ok = $true; error = $null; history = $null; dryRun = $true }
  }

  $submit = Invoke-RestMethod -Uri "$ComfyUiUrl/prompt" -Method Post -ContentType "application/json" -Body $payload
  if ($submit.node_errors -and $submit.node_errors.PSObject.Properties.Count -gt 0) {
    return @{ ok = $false; error = ("node_errors: " + ($submit.node_errors | ConvertTo-Json -Depth 5 -Compress)); history = $null }
  }
  $promptId = $submit.prompt_id
  Write-Host "  queued as $promptId"

  $deadline = (Get-Date).AddMinutes($TimeoutMin)
  while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds $PollSec
    try {
      $hist = Invoke-RestMethod -Uri "$ComfyUiUrl/history/$promptId" -TimeoutSec 3
      $entry = $hist.$promptId
      if ($entry) {
        if ($entry.status.completed -eq $true) {
          return @{ ok = $true; error = $null; history = $entry }
        }
        if ($entry.status.status_str -eq 'error') {
          return @{ ok = $false; error = ("comfyui error: " + ($entry.status | ConvertTo-Json -Depth 5 -Compress)); history = $entry }
        }
      }
    } catch { }
  }
  return @{ ok = $false; error = "timeout after $TimeoutMin min"; history = $null }
}
