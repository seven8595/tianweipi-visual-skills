# 优化项详细参考

本文件记录 `scan_health.ps1` 检测的每一项、`apply_changes.ps1` 执行的每个修复动作的具体含义、原理、回滚方法和风险边界。

> **硬约束**：本 Skill **不**禁用任何 Windows 系统服务（SysMain / Print Spooler / Windows Search 等）。用户风险容忍度 = 可逆安全项 + 防火墙规则，但不动服务。
> **硬约束**：所有写操作前自动创建系统还原点。

---

## 目录

- [网络 Network](#网络-network)
- [安全 Security](#安全-security)
- [稳定性 Stability](#稳定性-stability)
- [隐私 Privacy](#隐私-privacy)

---

## 网络 Network

### net_dns_optimize
- **作用**：把所有活动物理网卡的 IPv4 DNS 改为 `223.5.5.5`（阿里公共 DNS）+ `119.29.29.29`（腾讯 DNSPod）。
- **命令**：`Set-DnsClientServerAddress -InterfaceIndex <idx> -ServerAddresses ('223.5.5.5','119.29.29.29')`
- **回滚**：`Set-DnsClientServerAddress -InterfaceIndex <idx> -ResetServerAddresses`（自动获取）。
- **风险**：低。若你在公司内网需要内部 DNS，改回自动即可。
- **注意**：Clear-DnsClientCache 会清本地缓存，首次解析略慢。

### net_nic_power_disable
- **作用**：禁用网卡"允许计算机关闭此设备以节约电源"。
- **命令**：`Set-NetAdapterPowerManagement -Name <nic> -AllowComputerToTurnOffDevice Disabled`
- **回滚**：`AllowComputerToTurnOffDevice Enabled`。
- **风险**：低。笔记本续航略降，但不会出现合盖后断网、游戏中突然掉线。

### net_tcp_autotune_reset
- **作用**：把 TCP 接收窗口自动调谐级别重置为 `normal`。
- **命令**：`netsh interface tcp set global autotuninglevel=normal`
- **回滚**：`netsh interface tcp set global autotuninglevel=disabled`（一般不需要）。
- **风险**：低。被改为 disabled 会显著影响大带宽吞吐。

---

## 安全 Security

### sec_smb1_disable
- **作用**：禁用 SMBv1 协议。这是 EternalBlue / WannaCry 勒索病毒的主要攻击面。
- **命令**：
  - `Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart`
  - `Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force`
- **回滚**：`Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol`；`Set-SmbServerConfiguration -EnableSMB1Protocol $true -Force`。
- **风险**：中。仅当你需要访问 Windows XP / 老 NAS 的共享文件夹时会受影响。现代设备全部用 SMBv2/v3。

### sec_uac_max
- **作用**：把 UAC 调到最高级别（修改系统时始终通知并变暗桌面）。
- **注册表**：`HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\ConsentPromptBehaviorAdmin = 2`
- **回滚**：改回 `5`（默认，仅当程序修改设置时通知）。
- **风险**：低。会多弹几个 UAC 框，但更安全。

### sec_uac_enable
- **作用**：重新启用 UAC（当前被完全关闭时）。
- **注册表**：`EnableLUA = 1`，`ConsentPromptBehaviorAdmin = 2`
- **回滚**：无（启用 UAC 是正确状态）。
- **风险**：低。重启后生效。

### sec_defender_enable
- **作用**：开启 Windows Defender 实时保护。
- **命令**：`Set-MpPreference -DisableRealtimeMonitoring $false`
- **回滚**：`Set-MpPreference -DisableRealtimeMonitoring $true`。
- **风险**：低。如果你装了第三方杀软（火绒、卡巴等），Defender 会自动让位，不冲突。

### sec_fw_enable_{domain/private/public}
- **作用**：启用对应网络配置文件的 Windows 防火墙。
- **命令**：`Set-NetFirewallProfile -Name <Profile> -Enabled True`
- **回滚**：`-Enabled False`。
- **风险**：低。**公用网络必须开**；专用/域网络如果你有特殊端口映射要自己加规则。

### sec_rdp_disable
- **作用**：禁用远程桌面连接。
- **注册表**：`HKLM\System\CurrentControlSet\Control\Terminal Server\fDenyTSConnections = 1`
- **回滚**：改为 `0`。
- **风险**：中。如果你用 RDP 远程这台电脑，别关。用向日葵/ToDesk/Parsec 不受影响。

### sec_guest_disable
- **作用**：禁用 Guest 来宾账户。
- **命令**：`Disable-LocalUser -Name 'Guest'`
- **回滚**：`Enable-LocalUser -Name 'Guest'`。
- **风险**：低。现代 Windows 默认就禁用。

### sec_ports_block
- **作用**：在**公用网络**配置文件下，阻止 135(RPC)/139(NetBIOS)/445(SMB)/3389(RDP) 的入站连接。
- **命令**：为每个端口创建一条 `Block` 入站规则，仅作用于 `Public` profile。
- **回滚**：`Remove-NetFirewallRule -DisplayName "Block_Inbound_Port_<port>"`。
- **风险**：低。专用网络（家里/公司 WiFi）不受影响；只有在咖啡厅/酒店等公网时才拦截。
- **注意**：这条规则是**追加**，不会删除你已有的放行规则。

---

## 稳定性 Stability

### stab_startup_review
- **作用**：启动项 > 15 时提示。**不自动禁用**，因为哪些是必要的（输入法、显卡控制面板、杀软）只有用户知道。
- **操作**：打开任务管理器 → 启动 tab，自行禁用。
- **回滚**：在任务管理器里重新启用。

### stab_pagefile_auto
- **作用**：把虚拟内存改回"系统自动管理"。
- **命令**：`(Get-WmiObject Win32_ComputerSystem).AutomaticManagedPagefile = $true`
- **回滚**：在系统属性 → 高级 → 性能 → 虚拟内存里手动设回固定值。
- **风险**：低。自动管理是微软推荐设置。

### stab_autoreboot_off
- **作用**：蓝屏时不自动重启，停在 BSOD 画面让你抄下停止代码。
- **注册表**：`HKLM\SYSTEM\CurrentControlSet\Control\CrashControl\AutoReboot = 0`
- **回滚**：改回 `1`。
- **风险**：低。

### stab_dump_set
- **作用**：把蓝屏转储设为"自动内存转储"（7），平衡信息和磁盘占用。
- **注册表**：`CrashDumpEnabled = 7`
- **回滚**：改回 `2`（内核转储）或 `1`（完整转储）。
- **风险**：低。

### stab_8dot3_disable
- **作用**：禁用 NTFS 生成 8.3 短文件名（如 `PROGRA~1`）。
- **命令**：`fsutil behavior set disable8dot3 1`
- **回滚**：`fsutil behavior set disable8dot3 0`。
- **风险**：低。**仅**极少数 16 位老安装程序会失败。现代软件无影响。

---

## 隐私 Privacy

### priv_telemetry_min
- **作用**：把诊断数据级别降到"基本"(1)。
- **注册表**：`HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection\AllowTelemetry = 1`
- **回滚**：删除该值或改回 `3`。
- **风险**：低。企业版/教育版可设 0（安全），家庭版/专业版最低只能 1。

### priv_adid_off
- **作用**：关闭广告 ID（应用无法用广告 ID 跨应用追踪你）。
- **注册表**：`HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo\Enabled = 0`
- **回滚**：改回 `1`。
- **风险**：低。

### priv_bgapps_off
- **作用**：全局禁止 UWP 应用在后台运行。
- **注册表**：`HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications\GlobalDisabled = 1`
- **回滚**：改回 `0`。
- **风险**：低。邮件/日历 UWP 应用不会后台刷新，但桌面版（如 Outlook）不受影响。

### priv_activity_off
- **作用**：关闭 Windows 时间线/活动历史。
- **注册表**：`HKLM\SOFTWARE\Policies\Microsoft\Windows\System\EnableActivityFeed = 0`
- **回滚**：删除该值。
- **风险**：低。Alt+Tab 不再显示跨设备任务时间线。

### priv_tailored_off
- **作用**：关闭"基于诊断数据的定制体验"（开始菜单/设置里的推荐建议）。
- **注册表**：`HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy\TailoredExperiencesWithDiagnosticDataEnabled = 0`
- **回滚**：改回 `1`。
- **风险**：低。

### priv_location_deny
- **作用**：全局拒绝位置服务。
- **注册表**：`HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location\Value = "Deny"`
- **回滚**：改回 `"Allow"`。
- **风险**：中。地图、天气、外卖、打车类应用拿不到位置，需要手动开。

---

## 游戏 / 电源 / 锁屏（v2 新增）

### perf_gamedvr_off
- **作用**：关闭 Xbox Game Bar 的后台录制（Game DVR）。这个功能在后台持续录制，会吃掉游戏帧率，Dota/PUBG 尤其明显。
- **注册表**：
  - `HKCU\System\GameConfigStore\GameDVR_Enabled = 0`
  - `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR\AppCaptureEnabled = 0`
- **回滚**：改回 `1`。
- **风险**：低。只是不能用 Win+G 录屏；想录游戏用 OBS / NVIDIA ShadowPlay 更高效。

### perf_powerplan_high
- **作用**：把电源计划切到"高性能"（GUID `8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c`）。
- **命令**：`powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c`
- **回滚**：`powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e`（平衡）。
- **风险**：低。台式机插电建议高性能；笔记本用电池会更费电。

### sec_lock_set
- **作用**：开启屏保并设 30 分钟后自动锁屏 + 需要密码。
- **注册表**：`HKCU\Control Panel\Desktop`
  - `ScreenSaveActive = "1"`
  - `ScreenSaveTimeOut = "1800"`
  - `ScreenSaverIsSecure = "1"`
- **回滚**：`ScreenSaveActive = "0"`。
- **风险**：低。用户本机无他人接触，30 分钟是偏好设置；公共环境建议 5-10 分钟。

### stab_hiberfil_off
- **作用**：关闭休眠，删除 `hiberfil.sys`（通常占内存大小的空间，比如 32GB 内存就占 32GB）。
- **命令**：`powercfg /h off`
- **回滚**：`powercfg /h on`。
- **风险**：低。关闭后不能用"休眠"功能，但睡眠（S3/S0）不受影响；开机速度略快。

---

## 白帽深度加固（v3 新增）

### sec_lsa_ppl_enable
- **作用**：启用 LSA 保护（RunAsPPL），让 LSASS 进程以 Protected Process Light 运行，Mimikatz 等工具无法 openprocess 读取凭证。
- **注册表**：`HKLM\SYSTEM\CurrentControlSet\Control\Lsa\RunAsPPL = 1`
- **回滚**：删除该值。
- **风险**：中。某些老杀软/凭据提供方（指纹登录、智能卡）可能不兼容；重启后生效。
- **注意**：Win10 1607+ 原生支持。

### sec_wdigest_disable
- **作用**：禁用 WDigest 把明文凭证驻留内存。Win8.1+ 默认已禁用，但某些"优化工具"会重新打开。
- **注册表**：`HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\Wdigest\UseLogonCredential = 0`
- **回滚**：改回 1（不建议）。
- **风险**：低。

### sec_pagefile_clear_on
- **作用**：关机时清空 pagefile.sys，防止取证/物理接触从页面文件抓到凭证哈希。
- **注册表**：`HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\ClearPageFileAtShutdown = 1`
- **回滚**：改回 0。
- **风险**：低。关机变慢几秒。

### sec_limit_blank_enable
- **作用**：空密码账户只能本地交互登录，不能走 SMB/网络登录。
- **注册表**：`HKLM\SYSTEM\CurrentControlSet\Control\Lsa\LimitBlankPasswordUse = 1`
- **回滚**：改回 0（极度不建议）。
- **风险**：低。

### sec_aie_disable
- **作用**：关闭 AlwaysInstallElevated。这个开关如果开了，任何用户都能以 SYSTEM 权限安装 MSI，是本地提权核弹。
- **注册表**：`HKCU\...\Policies\Microsoft\Windows\Installer\AlwaysInstallElevated = 0` 和 HKLM 同路径。
- **回滚**：一般不需要回滚。
- **风险**：低。正常人/软件都不该开这个。

### sec_auto_logon_disable
- **作用**：关闭自动登录，并删除注册表里明文存的 DefaultPassword。
- **注册表**：`HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\AutoAdminLogon = "0"`，删除 `DefaultPassword`。
- **回滚**：重新配置自动登录（不建议）。
- **风险**：低。

### sec_smb_signing_require
- **作用**：要求 SMB 服务端必须签名，防 NTLM relay 中继攻击。
- **命令**：`Set-SmbServerConfiguration -RequireSecuritySignature $true -Force`
- **回滚**：`$false`。
- **风险**：中。极老的嵌入式设备/老 NAS 可能不支持 SMB 签名，会连不上共享。

### sec_ntlm_level_set
- **作用**：把 LmCompatibilityLevel 设为 3（仅发 NTLMv2，拒绝 LM/NTLMv1）。
- **注册表**：`HKLM\SYSTEM\CurrentControlSet\Control\Lsa\LmCompatibilityLevel = 3`
- **回滚**：改回 1（默认）。
- **风险**：中。老设备（XP、老打印机、老 NAS）可能认证失败。

### sec_restrict_anon_set
- **作用**：限制匿名/空会话枚举（不让未认证的人列用户、列共享）。
- **注册表**：`HKLM\SYSTEM\CurrentControlSet\Control\Lsa\RestrictAnonymous = 1`
- **回滚**：改回 0。
- **风险**：低。域环境可能需要 1，工作组 1 也安全。

### sec_appinit_clear
- **作用**：清空 AppInit_DLLs。这个值里列的 DLL 会被每个加载 user32.dll 的进程加载，是 malware 经典持久化点。
- **注册表**：`HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows\AppInit_DLLs = ""`（以及 WOW6432Node 路径）
- **回滚**：如果清之前记录了原值，写回去。
- **风险**：中。如果你知道是哪个软件加的（某些输入法/杀软），别清；否则空着是正确状态。

### sec_asr_enable
- **作用**：启用微软推荐的 9 条 ASR（Attack Surface Reduction）规则，Block 模式。拦截 Office 宏从邮件跑 exe、USB 跑 exe、JS/VBS 下载 exe、易受攻击驱动等。
- **命令**：`Set-MpPreference -AttackSurfaceReductionRules_Ids <9 GUIDs> -AttackSurfaceReductionRules_Actions <9个1>`
- **回滚**：`Set-MpPreference -AttackSurfaceReductionRules_Ids @()` 清空。
- **风险**：中。第一次可能误拦你正在用的破解软件/老工具；脚本会列出来，被拦了去 Windows 安全中心加白名单。

### sec_cfa_enable
- **作用**：启用受控文件夹访问（勒索软件防护），阻止未授权程序修改文档/图片/桌面。
- **命令**：`Set-MpPreference -EnableControlledFolderAccess Enabled`
- **回滚**：`Disabled`。
- **风险**：低。第一次用会弹窗让你放行常用软件（Office、压缩软件等）。

---

## 堡垒级 v4 新增

### sec_hosts_reset
- **作用**：把 hosts 文件重置为默认（只留 localhost），并先备份原文件为 `hosts.bak_<时间戳>`。
- **路径**：`C:\Windows\System32\drivers\etc\hosts`
- **回滚**：把 `.bak_时间戳` 文件改回 `hosts`。
- **风险**：中。如果你自己加过 hosts 屏蔽广告/绕过 DNS，会被清掉——先确认 hosts 内容真的可疑再执行。

### sec_hvci_enable
- **作用**：启用内存完整性（HVCI / Memory Integrity），阻止未签名内核驱动加载，防 rootkit。
- **注册表**：`HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity\Enabled = 1`
- **回滚**：删除该值或设 0。
- **风险**：中。老驱动（特别是老杀软、老游戏反作弊）可能不兼容导致蓝屏；需要重启。

### sec_smartscreen_on
- **作用**：把 SmartScreen 调到最高（RequireAdmin），下载 exe 后先做云端信誉检查。
- **注册表**：`HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\SmartScreenEnabled = "RequireAdmin"`
- **回滚**：改回 `Off`。
- **风险**：低。

### dev_ps_remotesigned
- **作用**：把 LocalMachine 级 PowerShell 执行策略设为 RemoteSigned。本地脚本可跑，从网上下载的脚本需签名。
- **命令**：`Set-ExecutionPolicy RemoteSigned -Scope LocalMachine -Force`
- **回滚**：`Set-ExecutionPolicy Restricted -Scope LocalMachine`。
- **风险**：低。开发者安全默认值；完全 Restricted 会让很多工具跑不了。



