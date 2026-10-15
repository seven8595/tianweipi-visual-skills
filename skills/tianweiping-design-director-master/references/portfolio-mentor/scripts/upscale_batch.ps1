# upscale_batch.ps1
# 用法: .\upscale_batch.ps1 -InputDir "C:\path\to\imgs" -OutputDir "F:\out" -TargetWidth 3600 -TargetHeight 4800 -DPI 300
# 依赖: Real-ESRGAN ncnn-vulkan exe (首次运行自动从 ghfast.top 镜像下载)
#        ComfyUI 自带 python_embeded 里的 PIL (用于缩放到目标尺寸和设 DPI)

param(
  [Parameter(Mandatory=$true)][string]$InputDir,
  [Parameter(Mandatory=$true)][string]$OutputDir,
  [int]$TargetWidth = 3600,
  [int]$TargetHeight = 4800,
  [int]$DPI = 300,
  [string]$Model = "realesrgan-x4plus",
  [int]$Scale = 4
)

$ErrorActionPreference = "Stop"
$workRoot = "F:\upscale_work"
$exe = "$workRoot\realesrgan-ncnn-vulkan.exe"
$py  = "C:\Users\seven\Desktop\ComfyUI_windows_portable\python_embeded\python.exe"

# 1. 确保 Real-ESRGAN 存在
if (-not (Test-Path $exe)) {
  New-Item -ItemType Directory -Force -Path $workRoot | Out-Null
  $zip = "$workRoot\realesrgan.zip"
  Write-Host "首次运行，下载 Real-ESRGAN..."
  curl.exe -L --connect-timeout 10 --max-time 180 -o $zip "https://ghfast.top/https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
  Expand-Archive $zip -DestinationPath $workRoot -Force
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$rawDir = "$workRoot\raw"
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

# 2. 找输入图
$imgs = Get-ChildItem $InputDir -File | Where-Object { $_.Extension -match '\.(png|jpg|jpeg|webp)$' }
Write-Host "找到 $($imgs.Count) 张图"

# 3. 超分
foreach ($img in $imgs) {
  $rawOut = Join-Path $rawDir ($img.BaseName + "_x$Scale.png")
  Write-Host "超分: $($img.Name)"
  & $exe -i $img.FullName -o $rawOut -n $Model -s $Scale -f png | Out-Null
}

# 4. 缩放到目标尺寸 + 设 DPI
$resizeScript = "$workRoot\resize.py"
@'
from PIL import Image
import os, sys
raw_dir, out_dir, tw, th, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
os.makedirs(out_dir, exist_ok=True)
for f in os.listdir(raw_dir):
    if not f.lower().endswith(".png"): continue
    img = Image.open(os.path.join(raw_dir, f))
    if img.size != (tw, th):
        img = img.resize((tw, th), Image.LANCZOS)
    out = os.path.join(out_dir, f)
    img.save(out, "PNG", dpi=(dpi, dpi))
    print(f"  {os.path.basename(out)}: {img.size}, {os.path.getsize(out)//1024} KB")
'@ | Out-File -FilePath $resizeScript -Encoding utf8

Write-Host "缩放到 ${TargetWidth}x${TargetHeight} @ ${DPI}DPI..."
& $py $resizeScript $rawDir $OutputDir $TargetWidth $TargetHeight $DPI

Write-Host "完成. 输出目录: $OutputDir"
