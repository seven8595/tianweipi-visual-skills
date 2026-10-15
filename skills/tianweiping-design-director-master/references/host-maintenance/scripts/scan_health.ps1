<#
.SYNOPSIS
  Read-only health scan for Windows network / security / stability / privacy.
  Outputs a JSON array to stdout. Does NOT modify anything.

.OUTPUTS
  JSON array of check items. Each item:
  {
    "id": "net_dns",
    "category": "network",
    "name": "DNS 服务器",
    "status": "ok|warning|danger|info|needs_admin",
    "current": "...",
    "recommended": "...",
    "risk": "low|medium|high",
    "reversible": true,
    "description": "...",
    "fix_id": "net_dns_optimize"
  }
#>

$ErrorActionPreference = 'SilentlyContinue'

# Detect admin
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$results = @()

function Add-Result {
  param(
    [string]$id,
    [string]$category,
    [string]$name,
    [string]$status,
    [string]$current,
    [string]$recommended,
    [string]$risk,
    [bool]$reversible,
    [string]$description,
    [string]$fix_id
  )
  $script:results += [PSCustomObject]@{
    id          = $id
    category    = $category
    name        = $name
    status      = $status
    current     = $current
    recommended = $recommended
    risk        = $risk
    reversible  = $reversible
    description = $description
    fix_id      = $fix_id
  }
}

# ============ NETWORK ============

# DNS
try {
  $dns = Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object { $_.ServerAddresses.Count -gt 0 } | Select-Object -First 3 InterfaceAlias, ServerAddresses
  $dnsStr = ($dns | ForEach-Object { "$($_.InterfaceAlias): $($_.ServerAddresses -join ', ')" }) -join ' | '
  $hasPublic = $dns | ForEach-Object { $_.ServerAddresses } | Where-Object { $_ -match '^(223\.5\.5\.5|119\.29\.29\.29|8\.8\.8\.8|1\.1\.1\.1)$' }
  if ($hasPublic) {
    Add-Result 'net_dns' 'network' 'DNS 服务器' 'ok' $dnsStr '223.5.5.5 + 119.29.29.29' 'low' $true '已使用公共 DNS' ''
  } else {
    Add-Result 'net_dns' 'network' 'DNS 服务器' 'warning' $dnsStr '223.5.5.5 + 119.29.29.29' 'low' $true '当前 DNS 可能为运营商默认，延迟较高或存在劫持' 'net_dns_optimize'
  }
} catch {
  Add-Result 'net_dns' 'network' 'DNS 服务器' 'info' '无法读取' '—' 'low' $true $_ ''
}

# NIC power management
try {
  $nics = Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' }
  $badNics = @()
  foreach ($nic in $nics) {
    $pm = Get-NetAdapterPowerManagement -Name $nic.Name -ErrorAction SilentlyContinue
    if ($pm.AllowComputerToTurnOffDevice -eq 'Enabled') { $badNics += $nic.Name }
  }
  if ($badNics.Count -eq 0) {
    Add-Result 'net_nic_power' 'network' '网卡电源管理' 'ok' '已禁用省电' '保持禁用' 'low' $true '网卡不会被系统为省电关闭' ''
  } else {
    Add-Result 'net_nic_power' 'network' '网卡电源管理' 'warning' "允许关闭: $($badNics -join ', ')" '禁用省电' 'low' $true '系统可能为省电断开网卡，导致游戏/远程时网络中断' 'net_nic_power_disable'
  }
} catch {
  Add-Result 'net_nic_power' 'network' '网卡电源管理' 'info' '无法读取' '—' 'low' $true $_ ''
}

# TCP autotuning
try {
  $tcp = netsh interface tcp show global | Select-String '自动调整级别|Auto-Tuning'
  $tcpStr = ($tcp -join ' ').Trim()
  if ($tcpStr -match 'normal|正常') {
    Add-Result 'net_tcp_autotune' 'network' 'TCP 自动调谐' 'ok' $tcpStr 'normal' 'low' $true 'TCP 接收窗口自动调谐正常' ''
  } else {
    Add-Result 'net_tcp_autotune' 'network' 'TCP 自动调谐' 'warning' $tcpStr 'normal' 'low' $true 'TCP 自动调谐被修改，可能影响大带宽吞吐' 'net_tcp_autotune_reset'
  }
} catch {
  Add-Result 'net_tcp_autotune' 'network' 'TCP 自动调谐' 'info' '无法读取' '—' 'low' $true $_ ''
}

# SMBv1
try {
  $smb1 = Get-SmbServerConfiguration -ErrorAction SilentlyContinue
  if ($smb1.EnableSMB1Protocol -eq $false) {
    Add-Result 'sec_smb1' 'security' 'SMBv1 协议' 'ok' '已禁用' '保持禁用' 'low' $true 'SMBv1 已禁用，防 WannaCry 类勒索' ''
  } else {
    Add-Result 'sec_smb1' 'security' 'SMBv1 协议' 'danger' '已启用' '禁用' 'high' $true 'SMBv1 是 EternalBlue / WannaCry 攻击面，应禁用' 'sec_smb1_disable'
  }
} catch {
  Add-Result 'sec_smb1' 'security' 'SMBv1 协议' 'needs_admin' '需要管理员' '禁用' 'high' $true '读取需要管理员权限' ''
}

# ============ SECURITY ============

# UAC
try {
  $uac = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -ErrorAction SilentlyContinue
  if ($uac.ConsentPromptBehaviorAdmin -eq 2 -and $uac.EnableLUA -eq 1) {
    Add-Result 'sec_uac' 'security' 'UAC 用户账户控制' 'ok' '最高级别' '保持' 'low' $true 'UAC 始终通知' ''
  } elseif ($uac.EnableLUA -eq 1) {
    Add-Result 'sec_uac' 'security' 'UAC 用户账户控制' 'warning' "ConsentPromptBehaviorAdmin=$($uac.ConsentPromptBehaviorAdmin)" '2（始终通知）' 'medium' $true 'UAC 级别偏低，修改系统时不会弹窗确认' 'sec_uac_max'
  } else {
    Add-Result 'sec_uac' 'security' 'UAC 用户账户控制' 'danger' '已禁用 (EnableLUA=0)' '启用' 'high' $true 'UAC 完全关闭，恶意程序可静默提权' 'sec_uac_enable'
  }
} catch {
  Add-Result 'sec_uac' 'security' 'UAC 用户账户控制' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# Defender real-time — check if a third-party AV is registered first
# v9 修复：注册表路径在 Win11 常不存在，改用 SecurityCenter2 WMI（非管理员可读）
try {
  $defender = Get-MpComputerStatus -ErrorAction SilentlyContinue
  $thirdPartyAv = @()
  try {
    Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction Stop |
      ForEach-Object {
        if ($_.displayName -and $_.displayName -notmatch 'Windows Defender|Microsoft Defender') {
          $thirdPartyAv += $_.displayName
        }
      }
  } catch { }
  if (-not $thirdPartyAv) {
    $avRoot = 'HKLM:\SOFTWARE\Microsoft\Windows Security Center\Provider\Av'
    if (Test-Path $avRoot) {
      Get-ChildItem $avRoot -ErrorAction SilentlyContinue | ForEach-Object {
        $props = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
        if ($props.DISPLAYVALUE -and $props.DISPLAYVALUE -notmatch 'Windows Defender|Microsoft Defender') {
          $thirdPartyAv += $props.DISPLAYVALUE
        }
      }
    }
  }
  if ($defender.RealTimeProtectionEnabled -eq $true) {
    Add-Result 'sec_defender_rt' 'security' 'Defender 实时保护' 'ok' '已开启' '保持' 'low' $true '' ''
  } elseif ($thirdPartyAv.Count -gt 0) {
    Add-Result 'sec_defender_rt' 'security' '杀软状态' 'ok' "第三方杀软: $($thirdPartyAv -join ', ')" '保持' 'low' $true 'Defender 自动让位给第三方杀软，正常' ''
  } else {
    Add-Result 'sec_defender_rt' 'security' 'Defender 实时保护' 'danger' '已关闭且无第三方杀软' '开启' 'high' $true '实时保护关闭且安全中心无其他杀软，裸奔状态' 'sec_defender_enable'
  }
} catch {
  Add-Result 'sec_defender_rt' 'security' 'Defender 实时保护' 'needs_admin' '需要管理员' '开启' 'high' $true '' ''
}

# Firewall profiles
foreach ($profile in @('Domain','Private','Public')) {
  try {
    $fw = Get-NetFirewallProfile -Name $profile -ErrorAction SilentlyContinue
    if ($fw.Enabled -eq $true) {
      Add-Result "sec_fw_$($profile.ToLower())" 'security' "防火墙 - $profile 配置文件" 'ok' '已启用' '保持' 'low' $true '' ''
    } else {
      Add-Result "sec_fw_$($profile.ToLower())" 'security' "防火墙 - $profile 配置文件" 'danger' '已禁用' '启用' 'high' $true "$profile 网络防火墙关闭，公网暴露风险" "sec_fw_enable_$($profile.ToLower())"
    }
  } catch {
    Add-Result "sec_fw_$($profile.ToLower())" 'security' "防火墙 - $profile 配置文件" 'needs_admin' '需要管理员' '启用' 'high' $true '' ''
  }
}

# RDP
try {
  $rdp = Get-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -ErrorAction SilentlyContinue
  if ($rdp.fDenyTSConnections -eq 1) {
    Add-Result 'sec_rdp' 'security' '远程桌面 (RDP)' 'ok' '已禁用' '保持禁用（除非需要）' 'low' $true 'RDP 是勒索/爆破高频入口' ''
  } else {
    Add-Result 'sec_rdp' 'security' '远程桌面 (RDP)' 'warning' '已启用' '禁用' 'medium' $true '如不使用远程桌面建议关闭；如需要请配合 NLA 和强密码' 'sec_rdp_disable'
  }
} catch {
  Add-Result 'sec_rdp' 'security' '远程桌面 (RDP)' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# Guest account
try {
  $guest = Get-LocalUser -Name 'Guest' -ErrorAction SilentlyContinue
  if ($guest.Enabled) {
    Add-Result 'sec_guest' 'security' '来宾账户' 'danger' '已启用' '禁用' 'medium' $true '来宾账户启用是常见横向移动入口' 'sec_guest_disable'
  } else {
    Add-Result 'sec_guest' 'security' '来宾账户' 'ok' '已禁用' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_guest' 'security' '来宾账户' 'needs_admin' '需要管理员' '禁用' 'medium' $true '' ''
}

# Dangerous ports listening — only report danger when firewall Public profile is OFF
try {
  $ports = @(135, 139, 445, 3389)
  $listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ports -contains $_.LocalPort -and $_.LocalAddress -ne '127.0.0.1' }
  $exposed = $listening | Where-Object { $_.LocalAddress -eq '0.0.0.0' -or $_.LocalAddress -eq '::' }
  $pubFw = Get-NetFirewallProfile -Name Public -ErrorAction SilentlyContinue
  if ($exposed) {
    $portList = ($exposed | Select-Object -ExpandProperty LocalPort -Unique) -join ','
    if ($pubFw.Enabled -eq $true) {
      Add-Result 'sec_ports' 'security' '危险端口监听' 'info' "监听 0.0.0.0: $portList（公网防火墙已拦截）" '可考虑加防火墙 Block 规则加固' 'low' $true '端口虽监听但公网防火墙已拦截；专用网络内仍可访问，属于 Windows 默认行为' ''
    } else {
      Add-Result 'sec_ports' 'security' '危险端口对外监听' 'danger' "监听 0.0.0.0: $portList 且公网防火墙关闭" '加 Block 规则 / 开防火墙' 'high' $true 'SMB/RPC/RDP 对公网完全暴露，极易被扫描爆破' 'sec_ports_block'
    }
  } else {
    Add-Result 'sec_ports' 'security' '危险端口对外监听' 'ok' '未对外暴露' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_ports' 'security' '危险端口对外监听' 'needs_admin' '需要管理员' '—' 'high' $true '' ''
}

# ============ STABILITY ============

# Startup items
try {
  $startup = Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue
  $count = ($startup | Measure-Object).Count
  if ($count -gt 15) {
    Add-Result 'stab_startup' 'stability' '启动项数量' 'warning' "$count 项" '建议 < 10 项' 'low' $true '启动项过多会拖慢开机和占用内存' 'stab_startup_review'
  } else {
    Add-Result 'stab_startup' 'stability' '启动项数量' 'ok' "$count 项" '< 15 项' 'low' $true '' ''
  }
} catch {
  Add-Result 'stab_startup' 'stability' '启动项数量' 'info' '无法读取' '—' 'low' $true $_ ''
}

# Pagefile
try {
  $cs = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue
  $pf = Get-CimInstance Win32_PageFileSetting -ErrorAction SilentlyContinue
  if ($cs.AutomaticManagedPagefile) {
    Add-Result 'stab_pagefile' 'stability' '虚拟内存' 'ok' '系统自动管理' '保持自动管理（推荐）' 'low' $true '' ''
  } elseif ($pf) {
    Add-Result 'stab_pagefile' 'stability' '虚拟内存' 'info' "固定: $($pf.Name) Init=$($pf.InitialSize) Max=$($pf.MaximumSize)" '系统自动管理' 'low' $true '固定页面文件可能导致 OOM 或空间浪费' 'stab_pagefile_auto'
  } else {
    Add-Result 'stab_pagefile' 'stability' '虚拟内存' 'warning' '无页面文件' '启用自动管理' 'medium' $true '无页面文件可能导致程序崩溃时无法转储和大内存程序 OOM' 'stab_pagefile_auto'
  }
} catch {
  Add-Result 'stab_pagefile' 'stability' '虚拟内存' 'info' '无法读取' '—' 'low' $true $_ ''
}

# Crash auto-reboot
try {
  $crash = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl' -ErrorAction SilentlyContinue
  if ($crash.AutoReboot -eq 1) {
    Add-Result 'stab_autoreboot' 'stability' '系统崩溃自动重启' 'warning' '开启' '关闭（便于看到 BSOD 代码）' 'low' $true '蓝屏时自动重启会错过错误代码' 'stab_autoreboot_off'
  } else {
    Add-Result 'stab_autoreboot' 'stability' '系统崩溃自动重启' 'ok' '已关闭' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'stab_autoreboot' 'stability' '系统崩溃自动重启' 'info' '无法读取' '—' 'low' $true $_ ''
}

# Dump type
try {
  $dump = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl' -Name CrashDumpEnabled -ErrorAction SilentlyContinue
  # 1=complete, 2=kernel, 3=small, 7=automatic
  $dumpMap = @{1='完整内存转储';2='内核转储';3='小内存转储(256KB)';7='自动'}
  $dumpStr = "$($dump.CrashDumpEnabled) = $($dumpMap[[int]$dump.CrashDumpEnabled])"
  if ($dump.CrashDumpEnabled -eq 2 -or $dump.CrashDumpEnabled -eq 7) {
    Add-Result 'stab_dump' 'stability' '蓝屏转储类型' 'ok' $dumpStr '内核/自动' 'low' $true '' ''
  } else {
    Add-Result 'stab_dump' 'stability' '蓝屏转储类型' 'warning' $dumpStr '内核转储 (2) 或自动 (7)' 'low' $true '小转储信息不足，难以分析蓝屏' 'stab_dump_set'
  }
} catch {
  Add-Result 'stab_dump' 'stability' '蓝屏转储类型' 'info' '无法读取' '—' 'low' $true $_ ''
}

# 8.3 short names
try {
  $fsutil = fsutil 8dot3name query 2>&1 | Out-String
  if ($fsutil -match '0|已启用') {
    Add-Result 'stab_8dot3' 'stability' '8.3 短文件名创建' 'info' '启用' '禁用（性能略升，旧软件需谨慎）' 'low' $true '禁用可略增 NTFS 性能，但某些老安装程序会失败' 'stab_8dot3_disable'
  } else {
    Add-Result 'stab_8dot3' 'stability' '8.3 短文件名创建' 'ok' '已禁用' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'stab_8dot3' 'stability' '8.3 短文件名创建' 'info' '无法读取' '—' 'low' $true $_ ''
}

# ============ PRIVACY ============

# Telemetry
try {
  $tele = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Name AllowTelemetry -ErrorAction SilentlyContinue
  # 0=security (Enterprise only), 1=basic, 2=enhanced, 3=full
  $teleMap = @{0='安全';1='基本';2='增强';3='完整'}
  if ($null -eq $tele -or $null -eq $tele.AllowTelemetry) {
    $teleStr = '未设置（默认=完整 3）'
    Add-Result 'priv_telemetry' 'privacy' '遥测级别' 'warning' $teleStr '基本 (1)' 'low' $true '默认开启完整遥测，建议降到基本' 'priv_telemetry_min'
  } else {
    $tv = [int]$tele.AllowTelemetry
    $teleStr = "$tv = $($teleMap[$tv])"
    if ($tv -le 1) {
      Add-Result 'priv_telemetry' 'privacy' '遥测级别' 'ok' $teleStr '基本 (1)' 'low' $true '' ''
    } else {
      Add-Result 'priv_telemetry' 'privacy' '遥测级别' 'warning' $teleStr '基本 (1)' 'low' $true '减少向微软发送诊断数据' 'priv_telemetry_min'
    }
  }
} catch {
  Add-Result 'priv_telemetry' 'privacy' '遥测级别' 'info' '无法读取' '—' 'low' $true $_ ''
}

# Advertising ID
try {
  $ad = Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo' -Name Enabled -ErrorAction SilentlyContinue
  if ($ad.Enabled -eq 0) {
    Add-Result 'priv_adid' 'privacy' '广告 ID' 'ok' '已关闭' '保持关闭' 'low' $true '' ''
  } else {
    Add-Result 'priv_adid' 'privacy' '广告 ID' 'warning' '已开启' '关闭' 'low' $true '关闭后应用无法跨应用追踪你投放广告' 'priv_adid_off'
  }
} catch {
  Add-Result 'priv_adid' 'privacy' '广告 ID' 'warning' '未设置(默认开启)' '关闭' 'low' $true '默认开启，建议关闭' 'priv_adid_off'
}

# Background apps
try {
  $bg = Get-ItemProperty 'HKCU:\Global\UserTasks' -ErrorAction SilentlyContinue
  $bg2 = Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications' -Name GlobalDisabled -ErrorAction SilentlyContinue
  if ($bg2.GlobalDisabled -eq 1) {
    Add-Result 'priv_bgapps' 'privacy' '后台应用全局' 'ok' '已禁用' '保持' 'low' $true '' ''
  } else {
    Add-Result 'priv_bgapps' 'privacy' '后台应用全局' 'warning' '允许后台运行' '禁用全局后台' 'low' $true '阻止 UWP 应用在后台刷新，省内存省电' 'priv_bgapps_off'
  }
} catch {
  Add-Result 'priv_bgapps' 'privacy' '后台应用全局' 'warning' '未设置(默认允许)' '禁用全局后台' 'low' $true '默认允许后台运行' 'priv_bgapps_off'
}

# Activity history
try {
  $act = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System' -Name EnableActivityFeed -ErrorAction SilentlyContinue
  if ($act.EnableActivityFeed -eq 0) {
    Add-Result 'priv_activity' 'privacy' '活动历史' 'ok' '已关闭' '保持' 'low' $true '' ''
  } else {
    Add-Result 'priv_activity' 'privacy' '活动历史' 'warning' '开启' '关闭' 'low' $true '时间线会记录你打开的文档和网站' 'priv_activity_off'
  }
} catch {
  Add-Result 'priv_activity' 'privacy' '活动历史' 'warning' '未设置(默认开启)' '关闭' 'low' $true '默认开启' 'priv_activity_off'
}

# Tailored experiences
try {
  $tailored = Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo' -ErrorAction SilentlyContinue
  $tailored2 = Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy' -Name TailoredExperiencesWithDiagnosticDataEnabled -ErrorAction SilentlyContinue
  if ($tailored2.TailoredExperiencesWithDiagnosticDataEnabled -eq 0) {
    Add-Result 'priv_tailored' 'privacy' '定制体验（基于诊断数据）' 'ok' '已关闭' '保持' 'low' $true '' ''
  } else {
    Add-Result 'priv_tailored' 'privacy' '定制体验（基于诊断数据）' 'warning' '开启' '关闭' 'low' $true '微软用你的诊断数据在开始菜单/提示里推建议' 'priv_tailored_off'
  }
} catch {
  Add-Result 'priv_tailored' 'privacy' '定制体验' 'warning' '未设置(默认开启)' '关闭' 'low' $true '默认开启' 'priv_tailored_off'
}

# Location service
try {
  $loc = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location' -Name Value -ErrorAction SilentlyContinue
  if ($loc.Value -eq 'Deny') {
    Add-Result 'priv_location' 'privacy' '系统定位服务' 'ok' '已拒绝' '保持（如不需要地图/天气）' 'low' $true '' ''
  } else {
    Add-Result 'priv_location' 'privacy' '系统定位服务' 'info' '允许' '如不需要地图/天气可拒绝' 'low' $true '定位服务会被 UWP 应用调用' 'priv_location_deny'
  }
} catch {
  Add-Result 'priv_location' 'privacy' '系统定位服务' 'info' '无法读取' '—' 'low' $true $_ ''
}

# ============ GAMING / POWER ============

# Game DVR background recording (causes stutter in games)
try {
  $gvr = Get-ItemProperty 'HKCU:\System\GameConfigStore' -Name GameDVR_Enabled -ErrorAction SilentlyContinue
  $appc = Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR' -Name AppCaptureEnabled -ErrorAction SilentlyContinue
  if ($gvr.GameDVR_Enabled -eq 0 -and $appc.AppCaptureEnabled -eq 0) {
    Add-Result 'perf_gamedvr' 'stability' 'Game DVR 后台录制' 'ok' '已关闭' '保持' 'low' $true '后台录制会吃掉游戏帧率' ''
  } else {
    Add-Result 'perf_gamedvr' 'stability' 'Game DVR 后台录制' 'warning' "GameDVR=$($gvr.GameDVR_Enabled) AppCapture=$($appc.AppCaptureEnabled)" '关闭' 'low' $true 'Xbox Game Bar 后台录制会导致游戏掉帧/卡顿，玩 Dota/PUBG 建议关' 'perf_gamedvr_off'
  }
} catch {
  Add-Result 'perf_gamedvr' 'stability' 'Game DVR 后台录制' 'info' '无法读取' '—' 'low' $true $_ ''
}

# Active power plan
try {
  $plan = powercfg /getactivescheme 2>&1 | Out-String
  if ($plan -match '高性能|High performance|卓越性能|Ultimate') {
    Add-Result 'perf_powerplan' 'stability' '电源计划' 'ok' $plan.Trim() '保持高性能' 'low' $true '' ''
  } elseif ($plan -match '平衡|Balanced') {
    Add-Result 'perf_powerplan' 'stability' '电源计划' 'info' $plan.Trim() '插电时建议高性能' 'low' $true '平衡模式会为了省电降 CPU/GPU 频率，台式机插电建议高性能' 'perf_powerplan_high'
  } else {
    Add-Result 'perf_powerplan' 'stability' '电源计划' 'warning' $plan.Trim() '高性能' 'low' $true '当前为省电模式，游戏/推理会降频' 'perf_powerplan_high'
  }
} catch {
  Add-Result 'perf_powerplan' 'stability' '电源计划' 'info' '无法读取' '—' 'low' $true $_ ''
}

# Screen saver lock (security: auto-lock after inactivity)
# User preference: solo machine, no one else around. 30 min timeout is fine.
try {
  $ss = Get-ItemProperty 'HKCU:\Control Panel\Desktop' -ErrorAction SilentlyContinue
  $active = $ss.ScreenSaveActive
  $timeout = [int]$ss.ScreenSaveTimeOut
  $isSecure = $ss.ScreenSaverIsSecure
  if ($active -eq '1' -and $timeout -le 1800 -and $isSecure -eq '1') {
    Add-Result 'sec_lock' 'security' '屏幕自动锁屏' 'ok' "${timeout}s 后锁屏" '保持 ≤30 分钟' 'low' $true '' ''
  } elseif ($active -eq '1' -and $isSecure -eq '1') {
    Add-Result 'sec_lock' 'security' '屏幕自动锁屏' 'info' "${timeout}s（建议 ≤1800s）" '30 分钟内锁屏' 'low' $true '你这里没人，超时也不影响；过短会打断你工作' 'sec_lock_set'
  } else {
    Add-Result 'sec_lock' 'security' '屏幕自动锁屏' 'warning' "屏保=$active 安全=$isSecure" '开启锁屏+需密码' 'low' $true '至少要有密码保护' 'sec_lock_set'
  }
} catch {
  Add-Result 'sec_lock' 'security' '屏幕自动锁屏' 'info' '无法读取' '—' 'low' $true $_ ''
}

# Hibernation file (hiberfil.sys)
try {
  $hiberFile = "$env:SystemDrive\hiberfil.sys"
  if (Test-Path $hiberFile) {
    $size = (Get-Item $hiberFile -Force).Length / 1GB
    if ($size -gt 8) {
      Add-Result 'stab_hiberfil' 'stability' '休眠文件 hiberfil.sys' 'info' ("{0:N1} GB" -f $size) '如不用休眠可关闭释放空间' 'low' $true '休眠文件通常 = 内存大小；不用休眠可用 powercfg /h off 释放' 'stab_hiberfil_off'
    } else {
      Add-Result 'stab_hiberfil' 'stability' '休眠文件 hiberfil.sys' 'ok' ("{0:N1} GB" -f $size) '—' 'low' $true '' ''
    }
  } else {
    Add-Result 'stab_hiberfil' 'stability' '休眠文件 hiberfil.sys' 'ok' '已关闭' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'stab_hiberfil' 'stability' '休眠文件 hiberfil.sys' 'info' '无法读取' '—' 'low' $true $_ ''
}

# ============ DEEP SECURITY AUDIT (white-hat level) ============

# --- LSA protection: RunAsPPL (blocks Mimikatz from reading LSASS) ---
try {
  $ppl = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name RunAsPPL -ErrorAction SilentlyContinue
  if ($ppl.RunAsPPL -eq 1) {
    Add-Result 'sec_lsa_ppl' 'security' 'LSA 保护 (RunAsPPL)' 'ok' '已启用' '保持' 'medium' $true 'LSASS 以 PPL 运行，Mimikatz 无法 dump' ''
  } else {
    Add-Result 'sec_lsa_ppl' 'security' 'LSA 保护 (RunAsPPL)' 'warning' '未启用' '启用' 'high' $true '未启用则恶意代码可读 LSASS 内存偷凭证' 'sec_lsa_ppl_enable'
  }
} catch {
  Add-Result 'sec_lsa_ppl' 'security' 'LSA 保护 (RunAsPPL)' 'needs_admin' '需要管理员' '启用' 'high' $true '' ''
}

# --- WDigest: prevent plaintext creds in memory ---
try {
  $wd = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\Wdigest' -Name UseLogonCredential -ErrorAction SilentlyContinue
  if ($null -eq $wd -or $wd.UseLogonCredential -eq 0) {
    Add-Result 'sec_wdigest' 'security' 'WDigest 明文凭证' 'ok' '已禁用' '保持' 'medium' $true '' ''
  } else {
    Add-Result 'sec_wdigest' 'security' 'WDigest 明文凭证' 'danger' 'UseLogonCredential=1' '禁用 (设 0)' 'high' $true '登录凭证会以明文驻留内存，经典 Mimikatz 向量' 'sec_wdigest_disable'
  }
} catch {
  Add-Result 'sec_wdigest' 'security' 'WDigest 明文凭证' 'needs_admin' '需要管理员' '禁用' 'high' $true '' ''
}

# --- Pagefile cleared at shutdown (prevents creds in pagefile) ---
try {
  $pf = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management' -Name ClearPageFileAtShutdown -ErrorAction SilentlyContinue
  if ($pf.ClearPageFileAtShutdown -eq 1) {
    Add-Result 'sec_pagefile_clear' 'security' '关机清理页面文件' 'ok' '已启用' '保持' 'low' $true '防止物理取证从 pagefile 抓到凭证哈希' ''
  } else {
    Add-Result 'sec_pagefile_clear' 'security' '关机清理页面文件' 'info' '未启用' '建议启用（关机变慢几秒）' 'low' $true '多用户/笔记本维修场景建议开' 'sec_pagefile_clear_on'
  }
} catch {
  Add-Result 'sec_pagefile_clear' 'security' '关机清理页面文件' 'needs_admin' '需要管理员' '—' 'low' $true '' ''
}

# --- LimitBlankPasswordUse: blank-pwd accounts can't logon over network ---
try {
  $lbp = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name LimitBlankPasswordUse -ErrorAction SilentlyContinue
  if ($lbp.LimitBlankPasswordUse -eq 1) {
    Add-Result 'sec_limit_blank' 'security' '空密码网络登录限制' 'ok' '已启用' '保持' 'medium' $true '' ''
  } else {
    Add-Result 'sec_limit_blank' 'security' '空密码网络登录限制' 'danger' '未启用' '启用' 'high' $true '空密码账户可被 SMB 远程登录，经典攻击面' 'sec_limit_blank_enable'
  }
} catch {
  Add-Result 'sec_limit_blank' 'security' '空密码网络登录限制' 'needs_admin' '需要管理员' '启用' 'high' $true '' ''
}

# --- AlwaysInstallElevated: MSI always runs as SYSTEM (trivial privesc) ---
try {
  $aie1 = Get-ItemProperty 'HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer' -Name AlwaysInstallElevated -ErrorAction SilentlyContinue
  $aie2 = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer' -Name AlwaysInstallElevated -ErrorAction SilentlyContinue
  if ($aie1.AlwaysInstallElevated -eq 1 -or $aie2.AlwaysInstallElevated -eq 1) {
    Add-Result 'sec_aie' 'security' 'AlwaysInstallElevated (MSI 提权)' 'danger' "HKCU=$($aie1.AlwaysInstallElevated) HKLM=$($aie2.AlwaysInstallElevated)" '全部设 0 / 删除' 'high' $true '任何用户都能以 SYSTEM 安装 MSI，等于给本地提权大门' 'sec_aie_disable'
  } else {
    Add-Result 'sec_aie' 'security' 'AlwaysInstallElevated (MSI 提权)' 'ok' '未启用' '保持' 'high' $true '' ''
  }
} catch {
  Add-Result 'sec_aie' 'security' 'AlwaysInstallElevated' 'info' '无法读取' '—' 'high' $true $_ ''
}

# --- AutoAdminLogon: plaintext password in registry ---
try {
  $aal = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name AutoAdminLogon -ErrorAction SilentlyContinue
  if ($aal.AutoAdminLogon -eq '1') {
    Add-Result 'sec_auto_logon' 'security' '自动登录 (AutoAdminLogon)' 'danger' '已启用' '禁用' 'high' $true '密码存在 DefaultPassword 注册表明文，任何人可读' 'sec_auto_logon_disable'
  } else {
    Add-Result 'sec_auto_logon' 'security' '自动登录 (AutoAdminLogon)' 'ok' '未启用' '保持' 'medium' $true '' ''
  }
} catch {
  Add-Result 'sec_auto_logon' 'security' '自动登录' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# --- SMB server-side signing required (anti-relay) ---
try {
  $smb = Get-SmbServerConfiguration -ErrorAction SilentlyContinue
  if ($smb.RequireSecuritySignature -eq $true) {
    Add-Result 'sec_smb_signing' 'security' 'SMB 服务端签名要求' 'ok' '已要求' '保持' 'medium' $true '防 SMB 中继攻击（NTLM relay）' ''
  } else {
    Add-Result 'sec_smb_signing' 'security' 'SMB 服务端签名要求' 'warning' '未要求' '启用（域环境必须）' 'medium' $true '中继攻击可偷 NTLM 哈希' 'sec_smb_signing_require'
  }
} catch {
  Add-Result 'sec_smb_signing' 'security' 'SMB 服务端签名要求' 'needs_admin' '需要管理员' '启用' 'medium' $true '' ''
}

# - LmCompatibilityLevel (disable LM/NTLMv1, enforce NTLMv2) ---
try {
  $lvl = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name LmCompatibilityLevel -ErrorAction SilentlyContinue
  $map = @{0='LM+NTLM';1='LM+NTLMv2';2='NTLMv1';3='NTLMv2';4='NTLMv2，拒绝LM';5='NTLMv2，拒绝LM+NTLMv1'}
  $v = if ($lvl) { [int]$lvl.LmCompatibilityLevel } else { '未设置(默认=0/1)' }
  if ($v -ge 3) {
    Add-Result 'sec_ntlm_level' 'security' 'NTLM 认证级别' 'ok' "$v = $map[$v]" '≥ 3' 'medium' $true '' ''
  } else {
    Add-Result 'sec_ntlm_level' 'security' 'NTLM 认证级别' 'warning' "$v = $map[$v]" '设 3（NTLMv2 only）' 'medium' $true 'LM/NTLMv1 易被破解和中继' 'sec_ntlm_level_set'
  }
} catch {
  Add-Result 'sec_ntlm_level' 'security' 'NTLM 认证级别' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# --- RestrictAnonymous (null session / IPC$) ---
try {
  $ra = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name RestrictAnonymous -ErrorAction SilentlyContinue
  if ($ra.RestrictAnonymous -eq 1 -or $ra.RestrictAnonymous -eq 2) {
    Add-Result 'sec_restrict_anon' 'security' '匿名/空会话限制' 'ok' "=$($ra.RestrictAnonymous)" '保持 ≥1' 'medium' $true '防止匿名枚举用户/共享' ''
  } else {
    Add-Result 'sec_restrict_anon' 'security' '匿名/空会话限制' 'warning' '=0' '设 1' 'medium' $true '空会话可枚举用户列表和共享名' 'sec_restrict_anon_set'
  }
} catch {
  Add-Result 'sec_restrict_anon' 'security' '匿名/空会话限制' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# --- Local Administrators group audit (who has SYSTEM rights on this box) ---
try {
  $admins = Get-LocalGroupMember -Group 'Administrators' -ErrorAction SilentlyContinue
  $names = ($admins | ForEach-Object { $_.Name }) -join ', '
  if ($admins.Count -le 2) {
    Add-Result 'sec_admin_members' 'security' '本地管理员组成员' 'ok' "$($admins.Count) 人: $names" '保持最小化' 'high' $true '列出来即可，不要自动删（可能误删必要账户）' ''
  } else {
    Add-Result 'sec_admin_members' 'security' '本地管理员组成员' 'warning' "$($admins.Count) 人: $names" '审计并移除不需要的' 'high' $true '每个额外管理员都是潜在入侵入口；去 设置→账户→其他用户 审查' ''
  }
} catch {
  Add-Result 'sec_admin_members' 'security' '本地管理员组成员' 'needs_admin' '需要管理员' '—' 'high' $true '' ''
}

# --- AppInit_DLLs (classic persistence / injection) ---
try {
  $ai = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows' -Name AppInit_DLLs -ErrorAction SilentlyContinue
  $ai2 = Get-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Windows' -Name AppInit_DLLs -ErrorAction SilentlyContinue
  $val = "$($ai.AppInit_DLLs) | WOW64: $($ai2.AppInit_DLLs)"
  if ([string]::IsNullOrWhiteSpace($ai.AppInit_DLLs) -and [string]::IsNullOrWhiteSpace($ai2.AppInit_DLLs)) {
    Add-Result 'sec_appinit' 'security' 'AppInit_DLLs 注入点' 'ok' '空' '保持空' 'high' $true '' ''
  } else {
    Add-Result 'sec_appinit' 'security' 'AppInit_DLLs 注入点' 'danger' $val '清空（除非你知道是哪个软件加的）' 'high' $true 'AppInit_DLLs 会被每个加载 user32.dll 的进程加载，是经典持久化；非软件安装后改的就是恶意软件' 'sec_appinit_clear'
  }
} catch {
  Add-Result 'sec_appinit' 'security' 'AppInit_DLLs' 'info' '无法读取' '—' 'high' $true $_ ''
}

# --- ASR (Attack Surface Reduction) rules ---
try {
  $asr = Get-MpPreference -ErrorAction SilentlyContinue
  $asrIds = $asr.AttackSurfaceReductionRules_Ids
  $asrActs = $asr.AttackSurfaceReductionRules_Actions
  if ($asrIds -and $asrIds.Count -gt 0) {
    $blocked = 0
    for ($i=0; $i -lt $asrIds.Count; $i++) { if ($asrActs[$i] -eq 1) { $blocked++ } }
    Add-Result 'sec_asr' 'security' 'ASR 攻击面缩减规则' 'ok' "$blocked / $($asrIds.Count) 条 Block" '保持' 'medium' $true '微软推荐的勒索/宏/ lateral movement 防护' ''
  } else {
    Add-Result 'sec_asr' 'security' 'ASR 攻击面缩减规则' 'info' '未配置' '建议启用推荐规则集' 'medium' $true 'ASR 能拦截 Office 宏、可执行文件从邮件运行、勒索软件行为' 'sec_asr_enable'
  }
} catch {
  Add-Result 'sec_asr' 'security' 'ASR 规则' 'needs_admin' '需要管理员' '—' 'medium' $true '' ''
}

# --- Controlled Folder Access (ransomware protection) ---
try {
  $cfa = Get-MpPreference -ErrorAction SilentlyContinue
  if ($cfa.EnableControlledFolderAccess -eq 1) {
    Add-Result 'sec_cfa' 'security' '受控文件夹访问 (勒索防护)' 'ok' '已启用' '保持' 'medium' $true '保护文档/图片/桌面不被勒索加密' ''
  } else {
    Add-Result 'sec_cfa' 'security' '受控文件夹访问 (勒索防护)' 'info' "状态=$($cfa.EnableControlledFolderAccess)" '建议启用' 'low' $true '启用后未授权程序不能改你的文档目录；第一次会问你放行哪些软件' 'sec_cfa_enable'
  }
} catch {
  Add-Result 'sec_cfa' 'security' '受控文件夹访问' 'needs_admin' '需要管理员' '—' 'low' $true '' ''
}

# --- Pending reboot from Windows Update ---
try {
  $reboot1 = Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired'
  $reboot2 = Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending'
  if ($reboot1 -or $reboot2) {
    Add-Result 'sec_pending_reboot' 'stability' '待重启（安全更新）' 'warning' '有补丁等重启' '尽快重启' 'low' $true '漏装的安全补丁是被打穿的常见原因' ''
  } else {
    Add-Result 'sec_pending_reboot' 'stability' '待重启（安全更新）' 'ok' '无' '—' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_pending_reboot' 'stability' '待重启' 'info' '无法读取' '—' 'low' $true $_ ''
}

# --- Shared folders audit ---
try {
  $shares = Get-SmbShare -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '^\w\$' -and $_.Name -ne 'IPC$' }
  if ($shares) {
    $shareNames = ($shares | ForEach-Object { $_.Name }) -join ', '
    Add-Result 'sec_shares' 'security' '显式共享文件夹' 'info' $shareNames '审计权限' 'medium' $true '非默认共享意味着你主动开了文件夹共享；公网防火墙开着不影响，但要确认 Everyone 组没写权限' ''
  } else {
    Add-Result 'sec_shares' 'security' '显式共享文件夹' 'ok' '无' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_shares' 'security' '显式共享文件夹' 'needs_admin' '需要管理员' '—' 'medium' $true '' ''
}

# ============ v9 HELPERS: read-only ACL writability test ============
# 判定目录能否被普通用户"新建文件"（用于把未加引号路径从误报变成真信号）
# 注意：AppendData(=建子目录) 不算可劫持，劫持需要 WriteData/CreateFiles(=建文件)。
# C:\ 根目录默认只给 Users AppendData，因此必须排除，否则全盘误报。
function Test-DirWritableByUser {
  param([string]$Dir)
  try {
    if (-not (Test-Path -LiteralPath $Dir -PathType Container)) { return $false }
    $acl = Get-Acl -LiteralPath $Dir -ErrorAction Stop
    $me = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    foreach ($ace in $acl.Access) {
      if ($ace.AccessControlType.ToString() -ne 'Allow') { continue }
      $id = $ace.IdentityReference.Value
      if ($id -match 'CREATOR OWNER|OWNER RIGHTS') { continue }
      $isBroad = $id -match '\\Users$|\\Users\b|Everyone|Authenticated Users|INTERACTIVE|\\Guest$'
      if (-not ($isBroad -or ($id -eq $me))) { continue }

      $bits = [int64]$ace.FileSystemRights
      $rights = $ace.FileSystemRights.ToString()
      # 建文件权限：WriteData(0x2) 位，或 Write / Modify / FullControl 组合
      $canCreateFile = (($bits -band 0x2) -ne 0) -or ($rights -match 'FullControl|Modify|\bWrite\b')
      if ($canCreateFile) { return $true }
    }
    return $false
  } catch { return $false }
}

# ============ FORTRESS LEVEL: ATTACK SURFACE ============

# --- Unquoted service path (classic local privesc) ---
# v9 优化：不再只看"路径含空格"，而是逐个前缀判定中间目录是否可被普通用户写入。
# 只有真正可写才报危险；厂商软件装在 Program Files 下的路径自动归为 ok。
try {
  $svcKeys = Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services' -ErrorAction SilentlyContinue
  $vuln = @()
  $benign = @()
  foreach ($k in $svcKeys) {
    $img = (Get-ItemProperty $k.PSPath -Name ImagePath -ErrorAction SilentlyContinue).ImagePath
    if (-not $img) { continue }
    if ($img -match '^"') { continue }            # 已加引号 = 安全
    if ($img -notmatch ' ') { continue }           # 无空格 = 无歧义
    if ($img -notmatch '^[A-Za-z]:\\') { continue } # 非本地绝对路径

    $parts = $img.Split(' ')
    $exploitable = $false
    $hit = ''
    for ($i = 1; $i -lt $parts.Count; $i++) {
      $prefix = ($parts[0..($i - 1)] -join ' ')
      if (Test-Path -LiteralPath $prefix -PathType Leaf) { break }   # 该位置已有文件，无法被抢注
      if (-not (Test-Path -LiteralPath $prefix)) {
        $parent = [System.IO.Path]::GetDirectoryName($prefix)
        if ($parent -and (Test-DirWritableByUser $parent)) {
          $exploitable = $true; $hit = $prefix; break
        }
        break
      }
    }
    if ($exploitable) { $vuln += "$($k.PSChildName) → $hit" } else { $benign += $k.PSChildName }
  }
  if ($vuln.Count -gt 0) {
    Add-Result 'sec_unquoted_svc' 'security' '未加引号服务路径（真可利用）' 'danger' "$($vuln.Count) 个可劫持: $($vuln -join '; ')" '给服务 ImagePath 加引号' 'high' $true '中间目录当前用户可写 → 可放恶意 exe 劫持服务启动并提权' ''
  } elseif ($benign.Count -gt 0) {
    Add-Result 'sec_unquoted_svc' 'security' '未加引号服务路径' 'ok' "$($benign.Count) 个含空格路径，中间目录均不可写" '无需处理' 'low' $true '厂商软件（腾讯/ACE 等）装在 Program Files 下，中间目录需管理员才能写，无法劫持' ''
  } else {
    Add-Result 'sec_unquoted_svc' 'security' '未加引号服务路径' 'ok' '未发现未加引号路径' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_unquoted_svc' 'security' '未加引号服务路径' 'info' '无法枚举' '—' 'low' $true $_ ''
}

# --- Overly permissive inbound firewall rules ---
# v9 优化：批量加载过滤表（原来逐条查 18s → 0.3s），并按"程序"归组让结果可操作
try {
  $afMap = @{}
  foreach ($f in (Get-NetFirewallAddressFilter -ErrorAction SilentlyContinue)) { $afMap[$f.InstanceID] = $f }
  $apMap = @{}
  foreach ($f in (Get-NetFirewallApplicationFilter -ErrorAction SilentlyContinue)) { $apMap[$f.InstanceID] = $f }

  $loose = @()
  foreach ($r in (Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True -ErrorAction SilentlyContinue)) {
    if ($r.Profile -notmatch 'Public') { continue }
    $af = $afMap[$r.InstanceID]
    if (-not $af) { continue }
    if ($af.RemoteAddress -ne 'Any') { continue }
    $loose += $r
  }

  if ($loose.Count -gt 5) {
    $groups = @{}
    foreach ($r in $loose) {
      $pf = $apMap[$r.InstanceID]
      $prog = if ($pf -and $pf.Program -and $pf.Program -ne 'Any') { Split-Path $pf.Program -Leaf } else { '系统/服务规则' }
      if (-not $groups.ContainsKey($prog)) { $groups[$prog] = 0 }
      $groups[$prog]++
    }
    $top = ($groups.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 5 |
            ForEach-Object { "$($_.Key)×$($_.Value)" }) -join ', '
    Add-Result 'sec_fw_loose' 'security' '公网防火墙宽松入站规则' 'warning' "$($loose.Count) 条 Allow Any（$top）" '先看归组，不认识的程序再禁用' 'medium' $true '公网任何人都能连这些端口；游戏/加速器/腾讯系通常可保留，陌生程序才需要处理' ''
  } else {
    Add-Result 'sec_fw_loose' 'security' '公网防火墙宽松入站规则' 'ok' "$($loose.Count) 条" '< 5 条' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_fw_loose' 'security' '公网防火墙宽松规则' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# --- Startup item signature check ---
try {
  $startup = Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue
  $unsigned = @()
  foreach ($s in $startup) {
    $cmd = $s.Command
    $parts = $cmd -split '"'
    if ($parts.Count -ge 2 -and $parts[1]) { $exe = $parts[1] } else { $exe = ($cmd -split ' ')[0] }
    if ($exe -and (Test-Path $exe -ErrorAction SilentlyContinue)) {
      $sig = Get-AuthenticodeSignature $exe -ErrorAction SilentlyContinue
      if ($sig.Status -ne 'Valid' -and $sig.Status -ne 'NotSigned') {
        $unsigned += "$($s.Name): $($sig.Status)"
      } elseif ($sig.Status -eq 'NotSigned') {
        $unsigned += "$($s.Name): 未签名"
      }
    }
  }
  if ($unsigned.Count -gt 0) {
    Add-Result 'sec_startup_sig' 'security' '启动项签名异常' 'warning' "$($unsigned.Count) 项: $($unsigned[0..([Math]::Min(2,$unsigned.Count-1))] -join '; ')" '审计这些程序是否可信' 'medium' $true '未签名/签名无效的启动项是 malware 常驻入口；你装的破解工具会触发，需人工判断' ''
  } else {
    Add-Result 'sec_startup_sig' 'security' '启动项签名异常' 'ok' '全部有效或未签名但路径已知' '保持' 'medium' $true '' ''
  }
} catch {
  Add-Result 'sec_startup_sig' 'security' '启动项签名' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# --- Hosts file audit ---
try {
  $hosts = "$env:SystemRoot\System32\drivers\etc\hosts"
  $lines = Get-Content $hosts -ErrorAction SilentlyContinue | Where-Object { $_ -notmatch '^\s*#' -and $_.Trim() -ne '' }
  $suspicious = $lines | Where-Object { $_ -match 'microsoft|windows|google|apple|facebook|bank|ali|taobao|qq|wechat' }
  if ($suspicious) {
    Add-Result 'sec_hosts' 'security' 'Hosts 文件可疑劫持' 'danger' ($suspicious -join '; ') '检查并删除' 'high' $true 'hosts 文件把系统/软件/银行域名指向了奇怪 IP，典型 malware 劫持' 'sec_hosts_reset'
  } else {
    Add-Result 'sec_hosts' 'security' 'Hosts 文件' 'ok' "$($lines.Count) 条自定义记录" '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_hosts' 'security' 'Hosts 文件' 'info' '无法读取' '—' 'low' $true $_ ''
}

# --- BitLocker status ---
try {
  $bl = Get-BitLockerVolume -ErrorAction SilentlyContinue | Where-Object { $_.VolumeType -eq 'OperatingSystem' }
  if ($bl -and $bl.ProtectionStatus -eq 'On') {
    Add-Result 'sec_bitlocker' 'security' 'BitLocker 磁盘加密' 'ok' '已启用' '保持' 'medium' $true '笔记本/移动设备丢失时防数据被直接读盘' ''
  } else {
    Add-Result 'sec_bitlocker' 'security' 'BitLocker 磁盘加密' 'info' '未启用' '台式机可不启用；笔记本建议开' 'low' $true 'BitLocker 防物理拆硬盘读数据；台式机放家里/办公室风险低' ''
  }
} catch {
  Add-Result 'sec_bitlocker' 'security' 'BitLocker' 'needs_admin' '需要管理员/家庭版不支持' '—' 'low' $true '' ''
}

# --- HVCI / Memory Integrity (kernel malware protection) ---
try {
  $dg = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' -ErrorAction SilentlyContinue
  if ($dg.Enabled -eq 1) {
    Add-Result 'sec_hvci' 'security' '内存完整性 (HVCI)' 'ok' '已启用' '保持' 'medium' $true '阻止未签名内核驱动加载，防 rootkit' ''
  } else {
    Add-Result 'sec_hvci' 'security' '内存完整性 (HVCI)' 'warning' '未启用' '建议启用' 'medium' $true '启用后防 rootkit 内核注入；老驱动可能不兼容，先在 Windows 安全中心开' 'sec_hvci_enable'
  }
} catch {
  Add-Result 'sec_hvci' 'security' '内存完整性' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# --- SmartScreen ---
try {
  $ss = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer' -Name SmartScreenEnabled -ErrorAction SilentlyContinue
  if ($ss.SmartScreenEnabled -eq 'RequireAdmin') {
    Add-Result 'sec_smartscreen' 'security' 'SmartScreen 筛选' 'ok' '警告/需要管理员' '保持' 'low' $true '下载 exe 后先云端信誉检查' ''
  } else {
    Add-Result 'sec_smartscreen' 'security' 'SmartScreen 筛选' 'warning' "$($ss.SmartScreenEnabled)" 'RequireAdmin' 'low' $true '关了会直接跑未知 exe' 'sec_smartscreen_on'
  }
} catch {
  Add-Result 'sec_smartscreen' 'security' 'SmartScreen' 'info' '无法读取' '—' 'low' $true $_ ''
}

# ============ DEV ENVIRONMENT HARDENING ============

# --- PowerShell execution policy ---
# v9 修复：原来只要任一作用域是 Undefined 就报 warning，而 CurrentUser=Undefined 是默认状态。
# 现在按"最具体作用域优先"解析出生效策略再判定。
try {
  $ep = Get-ExecutionPolicy -List
  $defined = $ep | Where-Object { $_.ExecutionPolicy -ne 'Undefined' }
  $epStr = if ($defined) { ($defined | ForEach-Object { "$($_.Scope)=$($_.ExecutionPolicy)" }) -join ', ' } else { '全部 Undefined' }

  $eff = ''
  # 注意：不要看 Process 作用域——扫描进程自己常用 -ExecutionPolicy Bypass 启动，会污染判定
  foreach ($scope in @('CurrentUser', 'LocalMachine', 'UserPolicy', 'MachinePolicy')) {
    $hit = $defined | Where-Object { $_.Scope -eq $scope } | Select-Object -First 1
    if ($hit) { $eff = $hit.ExecutionPolicy.ToString(); break }
  }

  if ($eff -eq 'RemoteSigned' -or $eff -eq 'AllSigned') {
    Add-Result 'dev_ps_exec' 'stability' 'PowerShell 执行策略' 'ok' "生效=$eff（$epStr）" 'RemoteSigned / AllSigned' 'low' $true '' ''
  } elseif ($eff -eq 'Unrestricted' -or $eff -eq 'Bypass') {
    Add-Result 'dev_ps_exec' 'stability' 'PowerShell 执行策略' 'warning' "生效=$eff（$epStr）" 'RemoteSigned' 'medium' $true 'Unrestricted/Bypass 下任意脚本可直接执行，恶意 .ps1 无门槛' 'dev_ps_remotesigned'
  } else {
    Add-Result 'dev_ps_exec' 'stability' 'PowerShell 执行策略' 'warning' "生效=$eff（$epStr）" 'RemoteSigned' 'low' $true 'Restricted/Undefined 会让开发工具和脚本跑不起来' 'dev_ps_remotesigned'
  }
} catch {
  Add-Result 'dev_ps_exec' 'stability' 'PowerShell 执行策略' 'info' '无法读取' '—' 'low' $true $_ ''
}

# --- SSH directory permissions (private key protection) ---
try {
  $sshDir = "$env:USERPROFILE\.ssh"
  if (Test-Path $sshDir) {
    $keys = Get-ChildItem $sshDir -Filter 'id_*' -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '\.pub$' }
    if ($keys) {
      Add-Result 'dev_ssh_perm' 'stability' 'SSH 私钥' 'ok' "$($keys.Count) 个私钥存在" '检查 ACL（Linux/WSL 下 600，Windows 上你独占）' 'low' $true 'Windows 上私钥权限由 NTFS ACL 控制；被其他用户读了就能冒充你' ''
    } else {
      Add-Result 'dev_ssh_perm' 'stability' 'SSH 私钥' 'info' '无 id_* 私钥' '—' 'low' $true '' ''
    }
  } else {
    Add-Result 'dev_ssh_perm' 'stability' 'SSH 私钥' 'info' '无 .ssh 目录' '—' 'low' $true '' ''
  }
} catch {
  Add-Result 'dev_ssh_perm' 'stability' 'SSH 私钥' 'info' '无法读取' '—' 'low' $true $_ ''
}

# ============ NETWORK HARDENING v6 (CIS 18.x / MSFT / NSA) ============

# RDP NLA (Network Level Authentication) - 必须开，防 BlueKeep 类无密码 RCE
try {
  $ts = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -ErrorAction SilentlyContinue
  $fDenyTS = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -ErrorAction SilentlyContinue).fDenyTSConnections
  if ($fDenyTS -eq 1) {
    Add-Result 'sec_rdp_nla' 'network' 'RDP 网络级身份验证 (NLA)' 'info' 'RDP 已禁用' '—' 'low' $true 'RDP 关了就无所谓 NLA' ''
  } else {
    if ($ts.UserAuthentication -eq 1 -and $ts.MinEncryptionLevel -ge 2) {
      Add-Result 'sec_rdp_nla' 'network' 'RDP 网络级身份验证 (NLA)' 'ok' "NLA=1 加密=$($ts.MinEncryptionLevel)" '保持' 'medium' $true '防未认证 RDP 协议攻击（BlueKeep 类）' ''
    } else {
      Add-Result 'sec_rdp_nla' 'network' 'RDP 网络级身份验证 (NLA)' 'warning' "NLA=$($ts.UserAuthentication) 加密=$($ts.MinEncryptionLevel)" '开 NLA + TLS' 'high' $true 'RDP 开着但没 NLA=网络上任何人可发起未认证 RDP 握手，历史上是 BlueKeep/DejaBlue 入口' 'sec_rdp_harden'
    }
  }
} catch {
  Add-Result 'sec_rdp_nla' 'network' 'RDP NLA' 'needs_admin' '需要管理员' '—' 'medium' $true '' ''
}

# NetBIOS over TCP/IP - 老协议，攻击者用来枚举共享/用户
try {
  $netbios = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces\Tcpip*' -ErrorAction SilentlyContinue
  if ($netbios) {
    $disabled = ($netbios | Where-Object { $_.NetbiosOptions -eq 2 }).Count
    $total = $netbios.Count
    if ($disabled -eq $total -and $total -gt 0) {
      Add-Result 'sec_netbios' 'network' 'NetBIOS over TCP/IP' 'ok' "全部 $total 个网卡已禁用" '保持禁用' 'medium' $true '防 NetBIOS 名称枚举和 SMB 中继' ''
    } else {
      Add-Result 'sec_netbios' 'network' 'NetBIOS over TCP/IP' 'warning' "$disabled/$total 个网卡禁用" '禁用所有网卡的 NetBIOS' 'medium' $true 'NetBIOS 广播可被响应毒化，也是老勒索家族的横向移动手段' 'sec_netbios_off'
    }
  }
} catch {
  Add-Result 'sec_netbios' 'network' 'NetBIOS' 'info' '无法读取' '—' 'low' $true $_ ''
}

# SMB Client Signing (不只是服务端)
try {
  $smbc = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters' -Name RequireSecuritySignature -ErrorAction SilentlyContinue
  if ($smbc.RequireSecuritySignature -eq 1) {
    Add-Result 'sec_smb_client_sign' 'network' 'SMB 客户端签名' 'ok' '已要求' '保持' 'medium' $true '防你访问恶意 SMB 共享时被中继' ''
  } else {
    Add-Result 'sec_smb_client_sign' 'network' 'SMB 客户端签名' 'warning' '未要求' '启用' 'medium' $true '攻击者开个恶意 SMB 服务器，你访问时 NTLM 哈希被中继' 'sec_smb_client_sign_on'
  }
} catch {
  Add-Result 'sec_smb_client_sign' 'network' 'SMB 客户端签名' 'needs_admin' '需要管理员' '—' 'medium' $true '' ''
}

# Netlogon 通道签名
try {
  $nl = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters' -Name SignSecureChannel -ErrorAction SilentlyContinue
  if ($nl.SignSecureChannel -eq 1) {
    Add-Result 'sec_netlogon_sign' 'network' 'Netlogon 安全通道签名' 'ok' '已启用' '保持' 'medium' $true '防域通道欺骗（工作组机也建议）' ''
  } else {
    Add-Result 'sec_netlogon_sign' 'network' 'Netlogon 安全通道签名' 'warning' '未启用' '启用' 'low' $true '' 'sec_netlogon_sign_on'
  }
} catch {
  Add-Result 'sec_netlogon_sign' 'network' 'Netlogon 签名' 'info' '无法读取' '—' 'low' $true '' ''
}

# 危险服务审计（只读，不自动改 - 用户红线是不碰服务）
$dangerSvcs = @('RemoteRegistry','TlntSvr','FTPSVC','FTPSc','simptcp','UPnP Device Host','WebClient','SessionEnv','TermService')
try {
  $running = @()
  foreach ($svc in $dangerSvcs) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($s -and $s.Status -eq 'Running') { $running += $svc }
  }
  if ($running.Count -eq 0) {
    Add-Result 'sec_danger_svc' 'network' '危险服务状态' 'ok' '无高危服务在跑' '保持' 'medium' $true 'RemoteRegistry/Telnet/UPnP/WebClient 都没开' ''
  } else {
    Add-Result 'sec_danger_svc' 'network' '危险服务状态' 'warning' "运行中: $($running -join ', ')" '审计并停掉不需要的' 'high' $true '这些是攻击面：远程注册表=别人能改你注册表；UPnP=路由器端口映射自动开；WebClient=WebDAV 客户端可被用来传文件' ''
  }
} catch {
  Add-Result 'sec_danger_svc' 'network' '危险服务' 'needs_admin' '需要管理员' '—' 'medium' $true '' ''
}

# WinRM 监听器
try {
  $winrm = Get-Service WinRM -ErrorAction SilentlyContinue
  if ($winrm -and $winrm.Status -eq 'Running') {
    $listeners = (winrm enumerate winrm/config/listener 2>&1 | Out-String)
    if ($listeners -match 'http.*5985|https.*5986') {
      Add-Result 'sec_winrm' 'network' 'WinRM 远程管理' 'warning' '服务运行中且有监听器' '如不用就停；用就加防火墙限制 IP' 'high' $true 'WinRM 是横向移动核心通道，攻击者拿到凭证后常用它远程执行' ''
    } else {
      Add-Result 'sec_winrm' 'network' 'WinRM 远程管理' 'info' '服务在跑但无监听器' '—' 'low' $true '' ''
    }
  } else {
    Add-Result 'sec_winrm' 'network' 'WinRM 远程管理' 'ok' '未运行' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_winrm' 'network' 'WinRM' 'info' '无法读取' '—' 'low' $true '' ''
}

# 出站防火墙默认策略
try {
  $fwOut = Get-NetFirewallProfile -ErrorAction SilentlyContinue | Where-Object { $_.DefaultOutboundAction -ne 'Allow' }
  if (-not $fwOut) {
    Add-Result 'sec_fw_outbound' 'network' '防火墙出站默认策略' 'ok' '默认允许（标准家用）' '保持' 'low' $true '家用机出站允许是正常；企业才用默认拒绝+白名单' ''
  } else {
    Add-Result 'sec_fw_outbound' 'network' '防火墙出站默认策略' 'warning' "$($fwOut.Name -join ',') DefaultOutbound=$($fwOut[0].DefaultOutboundAction)" '审计' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_fw_outbound' 'network' '防火墙出站策略' 'info' '无法读取' '—' 'low' $true '' ''
}

# ============ v5 ACADEMIC BASELINE: PASSWORD/AUDIT/PROTOCOL ============

# Password & lockout policy via `net accounts`
try {
  $na = net accounts 2>&1 | Out-String
  $pwdLen = if ($na -match '最小密码长度|Minimum password length\D+(\d+)') { [int]$Matches[1] } else { -1 }
  $lockout = if ($na -match '锁定阈值|Lockout threshold\D+(\d+)') { [int]$Matches[1] } else { -1 }

  if ($pwdLen -ge 14) {
    Add-Result 'sec_pwd_len' 'security' '最小密码长度' 'ok' "$pwdLen" '≥ 14' 'medium' $true '' ''
  } else {
    Add-Result 'sec_pwd_len' 'security' '最小密码长度' 'warning' "$pwdLen（CIS 建议 14）" '设 14' 'medium' $true '短密码易被暴力破解' 'sec_pwd_hardening'
  }

  if ($lockout -gt 0 -and $lockout -le 10) {
    Add-Result 'sec_lockout' 'security' '账户锁定阈值' 'ok' "$lockout 次失败" '5-10 次' 'medium' $true '' ''
  } elseif ($lockout -eq 0) {
    Add-Result 'sec_lockout' 'security' '账户锁定阈值' 'danger' '从不锁定（0）' '设 5 次失败后锁定' 'high' $true '无锁定阈值=在线暴力破解无门槛' 'sec_pwd_hardening'
  } else {
    Add-Result 'sec_lockout' 'security' '账户锁定阈值' 'warning' "$lockout 次" '建议 5' 'medium' $true '' 'sec_pwd_hardening'
  }
} catch {
  Add-Result 'sec_pwd_policy' 'security' '密码策略' 'info' '无法读取' '—' 'medium' $true $_ ''
}

# PowerShell Script Block Logging
try {
  $ps = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging' -ErrorAction SilentlyContinue
  if ($ps.EnableScriptBlockLogging -eq 1) {
    Add-Result 'audit_ps_logging' 'security' 'PowerShell 脚本块日志' 'ok' '已启用' '保持' 'medium' $true '事后可追溯攻击者跑了什么 PS 命令' ''
  } else {
    Add-Result 'audit_ps_logging' 'security' 'PowerShell 脚本块日志' 'warning' '未启用' '启用' 'medium' $true '出事时无法回溯攻击者执行的 PowerShell 命令' 'audit_ps_logging_on'
  }
} catch {
  Add-Result 'audit_ps_logging' 'security' 'PowerShell 脚本块日志' 'info' '无法读取' '—' 'medium' $true '' ''
}

# LLMNR 禁用
try {
  $llmnr = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient' -Name EnableMulticast -ErrorAction SilentlyContinue
  if ($llmnr.EnableMulticast -eq 0) {
    Add-Result 'sec_llmnr' 'network' 'LLMNR 多播名称解析' 'ok' '已禁用' '保持' 'medium' $true '防 NTLM relay 中间人攻击' ''
  } else {
    Add-Result 'sec_llmnr' 'network' 'LLMNR 多播名称解析' 'warning' '未禁用' '禁用' 'medium' $true 'LLMNR 响应可被恶意机器劫持，中继你的 NTLM 哈希' 'sec_llmnr_off'
  }
} catch {
  Add-Result 'sec_llmnr' 'network' 'LLMNR' 'info' '无法读取' '—' 'medium' $true '' ''
}

# 匿名 SAM 枚举
try {
  $anonsam = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name RestrictAnonymousSAM -ErrorAction SilentlyContinue
  if ($anonsam.RestrictAnonymousSAM -eq 1) {
    Add-Result 'sec_anon_sam' 'network' '匿名枚举 SAM 账户' 'ok' '已禁止' '保持' 'medium' $true '' ''
  } else {
    Add-Result 'sec_anon_sam' 'network' '匿名枚举 SAM 账户' 'warning' '未禁止' '禁止' 'high' $true '攻击者可空会话枚举你的所有用户名，针对性爆破' 'sec_anon_sam_block'
  }
} catch {
  Add-Result 'sec_anon_sam' 'network' '匿名枚举 SAM' 'info' '无法读取' '—' 'medium' $true '' ''
}

# 不存 LM hash
try {
  $lmhash = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name NoLMHash -ErrorAction SilentlyContinue
  if ($lmhash.NoLMHash -eq 1) {
    Add-Result 'sec_no_lmhash' 'security' '不存储 LM 哈希' 'ok' '已启用' '保持' 'medium' $true 'LM hash 可在几分钟内被破解' ''
  } else {
    Add-Result 'sec_no_lmhash' 'security' '不存储 LM 哈希' 'warning' '未启用' '启用' 'medium' $true 'LM 哈希极弱，偷到就能秒破' 'sec_no_lmhash_on'
  }
} catch {
  Add-Result 'sec_no_lmhash' 'security' '不存储 LM 哈希' 'info' '无法读取' '—' 'medium' $true '' ''
}

# 登录屏隐藏最后用户名
try {
  $nlu = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name DontDisplayLastUserName -ErrorAction SilentlyContinue
  if ($nlu.DontDisplayLastUserName -eq 1) {
    Add-Result 'sec_no_lastuser' 'security' '登录屏隐藏最后用户名' 'ok' '已启用' '保持' 'low' $true '' ''
  } else {
    Add-Result 'sec_no_lastuser' 'security' '登录屏隐藏最后用户名' 'info' '未启用' '可启用' 'low' $true '你本机无他人接触，低优先' 'sec_no_lastuser_on'
  }
} catch {
  Add-Result 'sec_no_lastuser' 'security' '登录屏隐藏最后用户名' 'info' '无法读取' '—' 'low' $true '' ''
}

# ============ v7 RED TEAM PERSISTENCE (MITRE ATT&CK T1053/T1546) ============

# 1. Suspicious scheduled tasks (powershell -enc, wget/curl, temp paths, unsigned publishers)
try {
  $tasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.State -ne 'Disabled' }
  $suspicious = @()
  foreach ($t in $tasks) {
    foreach ($a in $t.Actions) {
      $exec = "$($a.Execute) $($a.Arguments)"
      if ($exec -match '-enc\s+|-e\s+[A-Za-z0-9+/=]{20,}|Invoke-WebRequest|Invoke-Expression|IEX|DownloadString|DownloadFile|mshta|regsvr32.*scrobj|rundll32.*javascript' -and $exec -notmatch 'Microsoft|Windows|Google|OneDrive|Adobe|Nvidia|NVIDIA|Tencent|QQPC') {
        $suspicious += "$($t.TaskName): $exec".Substring(0, [Math]::Min(120, "$($t.TaskName): $exec".Length))
      }
    }
  }
  if ($suspicious.Count -eq 0) {
    Add-Result 'sec_schtasks' 'persistence' '可疑计划任务' 'ok' '无明显可疑项' '保持' 'medium' $true '红队最爱用 schtasks /create 持久化' ''
  } else {
    Add-Result 'sec_schtasks' 'persistence' '可疑计划任务' 'warning' "$($suspicious.Count) 个可疑: $($suspicious[0..([Math]::Min(2,$suspicious.Count-1))] -join ' | ')" '人工审查' 'high' $true '计划任务里有加密 PS / 下载命令 = 大概率后门' ''
  }
} catch {
  Add-Result 'sec_schtasks' 'persistence' '计划任务审计' 'info' '无法读取' '—' 'low' $true '' ''
}

# 2. WMI permanent event subscription (高级持久化，root\subscription 下)
# v9 优化：微软自带的订阅（SCM Event Log Filter 等）不再误报
try {
  $wmi = Get-CimInstance -Namespace root\subscription -ClassName __EventFilter -ErrorAction SilentlyContinue
  $wmiC = Get-CimInstance -Namespace root\subscription -ClassName CommandLineEventConsumer -ErrorAction SilentlyContinue
  if ($wmi -or $wmiC) {
    $names = @(($wmi.Name) + ($wmiC.Name)) | Where-Object { $_ }
    $suspect = $names | Where-Object { $_ -notmatch 'SCM|Microsoft|Windows|Defender|BVTFilter|WMI Filter|Event Log' }
    if ($suspect) {
      Add-Result 'sec_wmi_sub' 'persistence' 'WMI 永久事件订阅' 'warning' "可疑: $($suspect -join ', ')" '人工审查' 'high' $true '随机命名/带命令的 WMI 订阅是高级持久化（Goldmax/PowerStallion 类）' ''
    } else {
      Add-Result 'sec_wmi_sub' 'persistence' 'WMI 永久事件订阅' 'ok' "仅系统自带: $($names -join ', ')" '保持' 'low' $true 'SCM Event Log Filter 等是 Windows 组件，非后门' ''
    }
  } else {
    Add-Result 'sec_wmi_sub' 'persistence' 'WMI 永久事件订阅' 'ok' '无订阅' '保持' 'medium' $true '' ''
  }
} catch {
  Add-Result 'sec_wmi_sub' 'persistence' 'WMI 订阅' 'info' '无法读取' '—' 'low' $true '' ''
}

# 3. PowerShell v2 (老 PS 不受约束语言模式限制，攻击常用)
# v9 优化：Get-WindowsOptionalFeature 必须要管理员且失败很慢，非管理员直接跳过
if (-not $isAdmin) {
  Add-Result 'sec_psv2' 'security' 'PowerShell v2 引擎' 'needs_admin' '需要管理员' '检查后禁用' 'low' $true '' ''
} else {
try {
  $ps2 = Get-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2 -ErrorAction SilentlyContinue
  if ($ps2 -and $ps2.State -eq 'Enabled') {
    Add-Result 'sec_psv2' 'security' 'PowerShell v2 引擎' 'warning' '已启用' '禁用' 'medium' $true 'PS v2 无 AMR/约束语言，攻击者用 powershell -version 2 绕过防护' 'sec_psv2_disable'
  } else {
    Add-Result 'sec_psv2' 'security' 'PowerShell v2 引擎' 'ok' '已禁用' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_psv2' 'security' 'PowerShell v2' 'info' '无法读取' '—' 'low' $true '' ''
}
}

# 4. Stored credentials in Credential Manager (malware targets these)
try {
  $vault = cmdkey /list 2>&1 | Out-String
  $credCount = ([regex]::Matches($vault, 'Target:')).Count
  if ($credCount -gt 0) {
    Add-Result 'sec_cred_vault' 'security' 'Windows 凭据管理器' 'info' "$credCount 条已存凭据" '定期审查' 'low' $true '这些凭据被偷=直接登录，定期 cmdkey /list 看一眼' ''
  } else {
    Add-Result 'sec_cred_vault' 'security' 'Windows 凭据管理器' 'ok' '无存储凭据' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_cred_vault' 'security' '凭据管理器' 'info' '无法读取' '—' 'low' $true '' ''
}

# 5. Admin shares (ADMIN$ / C$) exposed
try {
  $shares = Get-SmbShare -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^\w+\$$|^ADMIN\$$|^IPC\$$' }
  if ($shares) {
    Add-Result 'sec_admin_share' 'network' '管理员隐藏共享' 'info' "$($shares.Name -join ', ')" '防火墙开着就没事' 'low' $true 'C$/ADMIN$/IPC$ 是默认管理共享，远程连需要管理员凭证' ''
  } else {
    Add-Result 'sec_admin_share' 'network' '管理员隐藏共享' 'ok' '无' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_admin_share' 'network' '管理员共享' 'info' '无法读取' '—' 'low' $true '' ''
}

# 6. PowerShell Transcription (full session recording)
try {
  $trans = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription' -ErrorAction SilentlyContinue
  if ($trans.EnableTranscripting -eq 1) {
    Add-Result 'audit_ps_transcript' 'security' 'PowerShell 全程转录' 'ok' '已启用' '保持' 'low' $true '所有 PS 会话记录到文件' ''
  } else {
    Add-Result 'audit_ps_transcript' 'security' 'PowerShell 全程转录' 'info' '未启用' '可选' 'low' $true '磁盘开销大，家用不必；脚本块日志已够' ''
  }
} catch {
  Add-Result 'audit_ps_transcript' 'security' 'PS 转录' 'info' '无法读取' '—' 'low' $true '' ''
}

# ============ v8 BOOT CHAIN / DEV EXPOSURE / WIRELESS ============

# 1. Secure Boot (UEFI rootkit protection)
try {
  $sb = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
  if ($sb -eq $true) {
    Add-Result 'sec_secureboot' 'boot' 'Secure Boot' 'ok' '已启用' '保持' 'medium' $true '防 bootkit/rootkit 加载未签名驱动' ''
  } elseif ($sb -eq $false) {
    Add-Result 'sec_secureboot' 'boot' 'Secure Boot' 'warning' '已关闭' '在 UEFI 里开启' 'medium' $true '关了 Secure Boot=恶意 bootkit 可在 Windows 启动前加载' ''
  } else {
    Add-Result 'sec_secureboot' 'boot' 'Secure Boot' 'info' 'Legacy BIOS 模式或无法读取' '—' 'low' $true '老 BIOS 不支持 Secure Boot' ''
  }
} catch {
  Add-Result 'sec_secureboot' 'boot' 'Secure Boot' 'info' '无法读取（非管理员或非 UEFI）' '—' 'low' $true '' ''
}

# 2. TPM presence
try {
  $tpm = Get-Tpm -ErrorAction SilentlyContinue
  if ($tpm -and $tpm.TpmPresent -and $tpm.TpmReady) {
    Add-Result 'sec_tpm' 'boot' 'TPM 芯片' 'ok' "v$($tpm.TpmVersion) present" '保持' 'low' $true 'BitLocker 和 Windows Hello 依赖 TPM' ''
  } else {
    Add-Result 'sec_tpm' 'boot' 'TPM 芯片' 'info' '无 TPM 或未就绪' '—' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_tpm' 'boot' 'TPM' 'info' '无法读取' '—' 'low' $true '' ''
}

# 3. OpenSSH Server running (port 22 exposure)
try {
  $ssh = Get-Service sshd -ErrorAction SilentlyContinue
  if ($ssh -and $ssh.Status -eq 'Running') {
    Add-Result 'sec_ssh_server' 'network' 'OpenSSH Server (sshd)' 'warning' '运行中（22 端口）' '如不用就停；用就配防火墙限 IP' 'high' $true 'SSH 公网暴露=爆破+漏损入口；攻击者拿到 root 密码直接进来' ''
  } else {
    Add-Result 'sec_ssh_server' 'network' 'OpenSSH Server (sshd)' 'ok' '未运行' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_ssh_server' 'network' 'OpenSSH Server' 'info' '无法读取' '—' 'low' $true '' ''
}

# 4. IIS / W3SVC web server running (家用不该有)
try {
  $iis = Get-Service W3SVC -ErrorAction SilentlyContinue
  if ($iis -and $iis.Status -eq 'Running') {
    Add-Result 'sec_iis' 'network' 'IIS Web 服务器' 'warning' '运行中（80/443）' '如不用就停' 'medium' $true '家用机跑 Web 服务器=多一个远程攻击面' ''
  } else {
    Add-Result 'sec_iis' 'network' 'IIS Web 服务器' 'ok' '未运行' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_iis' 'network' 'IIS' 'info' '无法读取' '—' 'low' $true '' ''
}

# 5. SQL Server / Express default instance (port 1433)
try {
  $sql = Get-Service -Name 'MSSQL*' -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' }
  if ($sql) {
    Add-Result 'sec_sql' 'network' 'SQL Server 服务' 'warning' "$($sql.Name -join ',') 运行中" '检查是否绑了 localhost' 'medium' $true '默认 SQL Express 常被忘改 sa 密码，是勒索家族最爱打的' ''
  } else {
    Add-Result 'sec_sql' 'network' 'SQL Server 服务' 'ok' '未运行' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_sql' 'network' 'SQL Server' 'info' '无法读取' '—' 'low' $true '' ''
}

# 6. Remote Assistance (msra.exe) enabled
try {
  $ra = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' -Name fAllowToGetHelp -ErrorAction SilentlyContinue
  if ($ra.fAllowToGetHelp -eq 1) {
    Add-Result 'sec_remote_assist' 'network' '远程协助' 'warning' '已启用' '不用就关' 'medium' $true '钓鱼/社工常用：骗你接受协助请求=别人直接操作你电脑' ''
  } else {
    Add-Result 'sec_remote_assist' 'network' '远程协助' 'ok' '已禁用' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_remote_assist' 'network' '远程协助' 'info' '无法读取' '—' 'low' $true '' ''
}

# 7. Proxy server settings (恶意代理劫持流量)
try {
  $proxy = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
  if ($proxy.ProxyEnable -eq 1 -and $proxy.ProxyServer) {
    Add-Result 'sec_proxy' 'network' '系统代理设置' 'info' "已设: $($proxy.ProxyServer)" '如不是你自己配的要警惕' 'low' $true '恶意软件常改代理劫持流量；不认识就去关' ''
  } else {
    Add-Result 'sec_proxy' 'network' '系统代理设置' 'ok' '未启用' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_proxy' 'network' '代理设置' 'info' '无法读取' '—' 'low' $true '' ''
}

# 8. Bluetooth discoverable (BlueBorne / near-field attacks)
try {
  $bt = Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'OK' }
  if ($bt) {
    Add-Result 'sec_bluetooth' 'hardware' '蓝牙适配器' 'info' "$($bt.Count) 个蓝牙设备可用" '不用时关' 'low' $true '蓝牙是近场攻击面；不用就从飞行模式或设备管理器关' ''
  } else {
    Add-Result 'sec_bluetooth' 'hardware' '蓝牙适配器' 'ok' '无蓝牙设备' '保持' 'low' $true '' ''
  }
} catch {
  Add-Result 'sec_bluetooth' 'hardware' '蓝牙' 'info' '无法读取' '—' 'low' $true '' ''
}

# ============ OUTPUT ============

# v9 优化：输出前做一次去重 + 生成可直接执行的行动清单
$dupIds = $results | Group-Object id | Where-Object { $_.Count -gt 1 } | Select-Object -ExpandProperty Name
$results = $results | Group-Object id | ForEach-Object { $_.Group[0] }

$actionable = $results | Where-Object {
  ($_.status -eq 'danger' -or $_.status -eq 'warning') -and $_.fix_id
} | Sort-Object @{Expression={ if ($_.status -eq 'danger') { 0 } else { 1 } }},
                @{Expression={ switch ($_.risk) { 'high' {0} 'medium' {1} default {2} } }} |
  Select-Object -First 10

$summary = [PSCustomObject]@{
  scanned_at    = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  host          = $env:COMPUTERNAME
  is_admin      = $isAdmin
  total         = @($results).Count
  ok            = @($results | Where-Object { $_.status -eq 'ok' }).Count
  warning       = @($results | Where-Object { $_.status -eq 'warning' }).Count
  danger        = @($results | Where-Object { $_.status -eq 'danger' }).Count
  needs_admin   = @($results | Where-Object { $_.status -eq 'needs_admin' }).Count
  duplicates    = @($dupIds)
  action_count  = @($actionable).Count
  actions       = @($actionable | ForEach-Object { [PSCustomObject]@{ fix_id = $_.fix_id; name = $_.name; status = $_.status; risk = $_.risk } })
  items         = @($results)
}

$summary | ConvertTo-Json -Depth 6
