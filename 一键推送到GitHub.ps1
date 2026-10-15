<#
一键把「田伟平视觉技能库 Codex 版」推送到 GitHub
用法：
    cd F:\_codex技能导出_20261015
    .\一键推送到GitHub.ps1 -Repo tianweiping-visual-skills

说明：
- 本机没有任何 git 凭据（无 ~/.gitconfig、cmdkey 里没有 github 条目），
  所以第一次推送时 Git Credential Manager 会弹出 GitHub 登录窗口，登录一次即可，之后免密。
- 脚本不会删除任何远程内容；若仓库已存在且有文件，push 可能被拒绝（非快进），
  此时脚本会提示你改用 `git pull --rebase origin master` 后重试，而不是强推。
#>
param(
    [string]$Repo = 'tianweiping-visual-skills',
    [string]$Branch = 'master',
    [string]$Owner = 'seven8595'
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

Write-Host ''
Write-Host '=== 田伟平视觉技能库 Codex 版 · 推送到 GitHub ===' -ForegroundColor Cyan
Write-Host "仓库： https://github.com/$Owner/$Repo"
Write-Host ''

# 0. 本地状态检查
$status = & git status --porcelain
if ($status) {
    Write-Host '⚠ 有未提交的改动，先提交：' -ForegroundColor Yellow
    & git add -A
    & git commit -m '更新技能库内容'
}
$files = & git ls-files
$sum = 0; foreach ($f in $files) { if (Test-Path $f) { $sum += (Get-Item $f).Length } }
Write-Host ("本地仓库：{0} 个文件 / {1:N2} MB / 分支 {2}" -f $files.Count, ($sum / 1MB), $Branch)
Write-Host ''

# 1. 远程仓库必须先在网页上建好（git 本身不能在 GitHub 上建仓库）
$remoteUrl = "https://github.com/$Owner/$Repo.git"
$exists = $false
try {
    $null = & git ls-remote $remoteUrl 2>&1
    if ($LASTEXITCODE -eq 0) { $exists = $true }
} catch { $exists = $false }

if (-not $exists) {
    Write-Host '步骤 1 · 先在 GitHub 上创建这个仓库' -ForegroundColor Cyan
    Write-Host '  打开下面的页面，仓库名填：' -NoNewline
    Write-Host $Repo -ForegroundColor Yellow
    Write-Host '  可见性选私有或公开；' -NoNewline
    Write-Host '不要' -ForegroundColor Yellow -NoNewline
    Write-Host '勾选 "Add a README file" / .gitignore / license（否则会产生冲突）。'
    Write-Host ''
    $newUrl = "https://github.com/new?name=$Repo"
    Write-Host "  页面地址：$newUrl"
    Start-Process $newUrl
    Write-Host ''
    Read-Host '建好仓库后按回车继续（首次推送会弹出 GitHub 登录窗口，登录一次即可）'
}

# 2. 设置 remote
& git remote remove origin 2>$null
& git remote add origin $remoteUrl
Write-Host '步骤 2 · remote 已设置' -ForegroundColor Cyan
& git remote -v
Write-Host ''

# 3. 推送
Write-Host '步骤 3 · 推送中（如弹出 GitHub 登录窗口，请完成登录）...' -ForegroundColor Cyan
& git push -u origin $Branch
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host '✗ 推送失败。若是 "non-fast-forward"/"rejected"，说明远程已有内容。' -ForegroundColor Red
    Write-Host '  先合并再推，不要用 --force：' -ForegroundColor Red
    Write-Host "      git pull --rebase origin $Branch" -ForegroundColor Yellow
    Write-Host "      git push -u origin $Branch" -ForegroundColor Yellow
    Write-Host '  若提示认证失败，请确认登录的账号是 ' -NoNewline -ForegroundColor Red
    Write-Host $Owner -ForegroundColor Yellow
    exit 1
}

Write-Host ''
Write-Host "✓ 完成：https://github.com/$Owner/$Repo" -ForegroundColor Green
