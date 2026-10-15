param(
    [string]$Repo = 'tianweiping-visual-skills',
    [string]$Branch = '',
    [string]$Owner = 'seven8595'
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    exit 1
}

function Get-CurrentBranch {
    $current = (& git branch --show-current 2>$null).Trim()
    if (-not $current) {
        Fail 'Current directory is not a valid Git repository, or HEAD is detached.'
    }
    return $current
}

Write-Host ""
Write-Host '=== Push visual skills repo to GitHub ===' -ForegroundColor Cyan
Write-Host "Repo: https://github.com/$Owner/$Repo"
Write-Host ""

$null = & git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) {
    Fail "Current directory is not a Git repository: $root"
}

if (-not $Branch) {
    $Branch = Get-CurrentBranch
}

$status = & git status --porcelain
if ($status) {
    Write-Host '[WARN] Working tree has uncommitted changes; staging and committing first.' -ForegroundColor Yellow
    & git add -A
    $staged = @(& git diff --cached --name-only)
    if ($staged.Count -gt 0) {
        & git commit -m '更新技能库内容'
        if ($LASTEXITCODE -ne 0) {
            Fail 'git commit failed. Resolve the commit problem and retry.'
        }
    }
    if ($staged.Count -eq 0) {
        Write-Host '  git add -A ran, but there is nothing staged to commit; skipping commit.' -ForegroundColor DarkYellow
    }
}

$files = @(& git ls-files)
$sum = 0
foreach ($f in $files) {
    if (Test-Path $f) {
        $sum += (Get-Item $f).Length
    }
}
Write-Host ("Local repository: {0} tracked files / {1:N2} MB / branch {2}" -f $files.Count, ($sum / 1MB), $Branch)
Write-Host ""

$remoteUrl = "https://github.com/$Owner/$Repo.git"
$exists = $false
try {
    $null = & git ls-remote $remoteUrl 2>&1
    if ($LASTEXITCODE -eq 0) {
        $exists = $true
    }
} catch {
    $exists = $false
}

if (-not $exists) {
    Write-Host 'Step 1: create the repository on GitHub first.' -ForegroundColor Cyan
    Write-Host '  Open this page and use repo name: ' -NoNewline
    Write-Host $Repo -ForegroundColor Yellow
    Write-Host '  Visibility can be private or public; ' -NoNewline
    Write-Host 'do not' -ForegroundColor Yellow -NoNewline
    Write-Host ' initialize it with README, .gitignore, or license.'
    Write-Host ""
    $newUrl = "https://github.com/new?name=$Repo"
    Write-Host "  URL: $newUrl"
    Start-Process $newUrl
    Fail 'GitHub repository does not exist yet. Create it in the opened browser page, then rerun this script.'
}

& git remote remove origin 2>$null
& git remote add origin $remoteUrl
Write-Host 'Step 2: remote configured.' -ForegroundColor Cyan
& git remote -v
Write-Host ""

Write-Host 'Step 3: pushing now. If GitHub login opens, complete it.' -ForegroundColor Cyan
& git rev-parse --verify $Branch 2>$null
if ($LASTEXITCODE -ne 0) {
    Fail "Local branch does not exist: $Branch"
}

& git push -u origin $Branch
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host '[FAIL] Push failed. If you see non-fast-forward/rejected, the remote already has content.' -ForegroundColor Red
    Write-Host '  Rebase and push again; do not force push:' -ForegroundColor Red
    Write-Host "      git pull --rebase origin $Branch" -ForegroundColor Yellow
    Write-Host "      git push -u origin $Branch" -ForegroundColor Yellow
    Write-Host '  If authentication failed, confirm the logged-in GitHub account is ' -NoNewline -ForegroundColor Red
    Write-Host $Owner -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Done: https://github.com/$Owner/$Repo" -ForegroundColor Green
