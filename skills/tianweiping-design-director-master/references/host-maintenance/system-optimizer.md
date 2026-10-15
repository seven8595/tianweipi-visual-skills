---
name: system-optimizer
description: AI 创作工作流的系统性能诊断与释放。开机慢、内存吃紧、磁盘红、生图上传卡、后台偷跑时触发。自动识别 Windows/macOS/Linux 云 VM，跑只读盘点→清临时文件→备份并禁用不必要自启→给代理直连规则。不删用户文件、不卸载程序、不改系统核心服务。触发词：优化电脑、加速、释放内存、清磁盘、开机慢、卡顿、后台程序、网络慢、生图上传慢、启动项、临时文件。
---

# 系统性能释放（AI 创作工作流专用，跨平台）

## ⚡ 第一步：识别环境再动手

```powershell
# Windows 上先判断
$osInfo = Get-CimInstance Win32_OperatingSystem
if ($osInfo.Caption -like "*Windows*") { "→ Windows 分支" }
```

| 环境 | 优化空间 | 动作 |
|---|---|---|
| **用户 Windows 主机**（RTX 5080 那台） | 大：启动项、临时文件、代理、磁盘 | 走下面 Windows 完整流程 |
| **macOS** | 中：登录项、临时文件、DNS | 走 macOS 分支 |
| **Linux 云 VM / 沙箱** | 小：文件系统只读，不能装东西 | 只读盘点+清自己的临时文件，不动系统 |
| **手机端远程** | 无：只是终端 | 不跑本机优化，只看连接的主机状态 |

**铁律**：
- 不删用户文件（文档/下载/桌面/素材/工程）
- 不卸载程序，只禁开机自启
- 改配置前先备份
- 不碰系统服务和驱动
- 不自动重启
- 云 VM 里不装 sudo/apt/docker/systemctl（权限不够也不该装）

---

## A. Windows 主机（主战场）

### A.1 只读盘点
```powershell
$os = Get-CimInstance Win32_OperatingSystem
"内存: 总 $([math]::Round($os.TotalVisibleMemorySize/1MB,1))GB  可用 $([math]::Round($os.FreePhysicalMemory/1MB,1))GB"
Get-PSDrive C | ForEach-Object { "C盘: 已用 $([math]::Round($_.Used/1GB,1))GB  可用 $([math]::Round($_.Free/1GB,1))GB" }
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 ProcessName, @{n='MB';e={[math]::Round($_.WorkingSet64/1MB)}}
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader
Test-Connection www.doubao.com -Count 3 | Measure-Object ResponseTime -Average
Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" | Select-Object * -ExcludeProperty PS*
```

### A.2 安全清理
```powershell
ipconfig /flushdns
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
```
不清：回收站、微信/QQ 缓存、浏览器缓存、Windows Update 缓存。

### A.3 启动项管理
备份到桌面再动：
```powershell
$bak = "C:\Users\$env:USERNAME\Desktop\启动项备份_$(Get-Date -Format yyyyMMdd)"
New-Item -ItemType Directory -Force $bak | Out-Null
reg export "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" "$bak\HKCU.reg" /y
reg export "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" "$bak\HKLM.reg" /y
```

默认建议禁：
- 游戏平台：Steam、EADM、Razer 托盘、ACE-Tray
- 下载/网盘：迅雷、百度网盘、OneDrive
- 视频客户端：优酷、腾讯视频、爱奇艺
- 不常用：抖音托盘、Coze 扣子、Edge 预启动、Ollama（不用本地模型时）

必须留：
- 豆包、剪映、微信
- SecurityHealth、Realtek 音频、显卡

禁用：`Remove-ItemProperty "HKCU:\...\Run" -Name "项名"`
恢复：双击备份的 .reg。

---

## B. macOS

### B.1 盘点
```bash
top -l 1 -n 10 -o mem           # 内存占用前10
vm_stat | head -20               # 内存统计
df -h /                          # 磁盘
networkquality -v 2>/dev/null    # 网络质量（macOS 自带）
# 登录项
osascript -e 'tell application "System Events" to get the name of every login item'
```

### B.2 清理
```bash
sudo purge                       # 清内存缓存（可选，需密码）
rm -rf ~/Library/Caches/*       # 只清用户缓存，不动系统
```

### B.3 登录项
- 系统设置 → 通用 → 登录项，删掉不用的
- 不直接改 LaunchAgents，容易搞坏

---

## C. Linux 云 VM / 沙箱

**这种环境文件系统大部分只读，不能装东西。** 能做的：

```bash
free -h                          # 内存
df -h .                          # 磁盘
ps aux --sort=-%mem | head -10   # 占内存前10
uptime                           # 负载
du -sh ~/.cache 2>/dev/null      # 自己的缓存
```

能清的只有用户自己的缓存：
```bash
rm -rf ~/.cache/pip 2>/dev/null
rm -rf ~/.npm/_cacache 2>/dev/null
```

**不能做**：apt install、sudo systemctl、改内核参数、动 /etc。
如果这个环境卡，告诉用户"云 VM 资源有限，建议在 Windows 主机上跑重活"，不要硬优化。

---

## D. 代理直连规则（所有平台通用）

用户用 Clash/Mihomo/Clash Verge 时，国内 AI 服务走代理绕远。加在配置最上面：

```yaml
rules:
  - DOMAIN-SUFFIX,doubao.com,DIRECT
  - DOMAIN-SUFFIX,bytedance.com,DIRECT
  - DOMAIN-SUFFIX,doubaocdn.com,DIRECT
  - DOMAIN-SUFFIX,byteimg.com,DIRECT
  - DOMAIN-SUFFIX,volces.com,DIRECT
  - DOMAIN-SUFFIX,jianying.com,DIRECT
  - DOMAIN-SUFFIX,douyin.com,DIRECT
  - DOMAIN-SUFFIX,feishu.cn,DIRECT
```

判断：到 www.doubao.com 的 ping 如果 >20ms 但国内其他站正常，大概率走了代理。

---

## E. 输出格式

跑完给一张表：

| 项目 | 之前 | 之后 |
|---|---|---|
| 可用内存 | X GB | Y GB |
| 磁盘可用 | X GB | Y GB |
| 自启/登录项数量 | X 个 | Y 个 |
| 到豆包延迟 | X ms | Y ms |

加三句话：
1. 重启后效果才完全生效
2. 备份在哪，怎么恢复
3. 哪些没动、为什么（权限不够/涉及用户数据/云 VM 只读）

---

## F. 永远不做的事
- 不杀当前会话里正在跑的用户程序（微信、浏览器、剪辑软件）
- 不删 node_modules、conda 环境、ComfyUI 模型、素材工程
- 不改系统服务、驱动、内核参数
- 不装"优化大师""管家"类软件
- 不自动重启、不自动注销
- 云 VM 里不用 sudo/apt/docker
