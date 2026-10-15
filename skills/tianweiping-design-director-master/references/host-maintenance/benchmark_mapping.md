# 权威基线对照表（benchmark_mapping）

把本 skill 的 77 个检查项映射到四个权威基线，用来回答两个问题：

1. 这个检查项**凭什么**这么要求？（有没有权威依据，还是我的个人偏好）
2. 这台机器离工业界标准还差多远？（差距清单，可用于汇报/过审）

---

## 一、引用的基线及版本

| 代号 | 名称 | 版本口径 |
|---|---|---|
| **CIS** | CIS Microsoft Windows 11 Enterprise Benchmark | v3.0.0（v2.0.0 编号有偏移，见下方警告） |
| **MSS** | Microsoft Security Baseline for Windows 11 | 24H2 版本（Microsoft Security Compliance Toolkit） |
| **NIST** | NIST SP 800-53 Rev.5 | 控制项编号用 Rev.5 |
| **等保** | GB/T 22239-2019 网络安全等级保护基本要求 | 第三级安全要求 |

> **CIS 编号警告**：CIS 会随 benchmark 版本重排编号。v2.0.0 的 `2.3.11.x` 到 v3.0.0 可能变成 `2.3.x`。
> **稳定的标识是控制项名称，不是编号。** 本表同时给编号和名称，比对时以名称为准。
>
> **诚实标注**：标「类别对应」的是同类安全目标，不是逐字等价；标「无」的是该基线确实没有覆盖，不要硬凑。

---

## 二、身份鉴别与口令（差距最大的一组）

| check id | 本项检查 | CIS | MSS | NIST | 等保三级 |
|---|---|---|---|---|---|
| `sec_pwd_len` | 最小密码长度（建议 14） | **1.1.4** Minimum password length ≥ 14 | ✔ Password length | IA-5 | 8.1.4.1 a) |
| `sec_pwd_policy` | 密码历史 / 复杂度 | **1.1.1** Enforce password history = 24；**1.1.5** Password must meet complexity | ✔ | IA-5 | 8.1.4.1 a) |
| `sec_lockout` | 账户锁定策略 | **1.2.1** 锁定时长 ≥ 15 min；**1.2.2** 阈值 ≤ 10；**1.2.3** 计数器重置 ≥ 15 min | ✔ | **AC-7** Unsuccessful Logon Attempts | 8.1.4.1 c) |
| `sec_limit_blank` | 禁止空密码远程登录 | **2.3.1.x** Accounts: Limit local account use of blank passwords to console logon only = Enabled | ✔ | IA-5 | 8.1.4.1 a) |
| `sec_auto_logon` | 存储的自动登录凭据 | 类别对应 `2.3.1.x`（Autologon 属高价值凭据泄露点） | ✔ | IA-5、AC-7 | 8.1.4.1 |
| `sec_no_lastuser` | 不显示上次登录用户名 | **2.3.7.x** Interactive logon: Do not display last user name = Enabled | ✔ | IA-6（类别对应） | 8.1.4.2 |
| `sec_lock` | 无操作自动锁屏 | **2.3.7.x** Interactive logon: Machine inactivity limit ≤ 900 秒 | ✔ | **AC-11** Session Lock | 8.1.4.1 b) |
| `sec_cred_vault` | 凭据管理器残留 | 类别对应 `18.x`（凭据暴露面） | 无 | IA-5 | 8.1.4.1 |
| `sec_psv2` | 禁用 PowerShell v2 引擎 | **18.x** Disable PowerShell 2.0 | ✔ | CM-7 | 8.1.4.4 |
| `sec_dev_ps_exec` / `dev_ps_exec` | 执行策略 = RemoteSigned/AllSigned | **18.x** PowerShell Execution Policy | ✔ | CM-7 | 8.1.4.4 |
| `sec_ssh_perm` / `dev_ssh_perm` | SSH 私钥目录权限 | CIS 无（Linux 基线有） | 无 | IA-5、AC-6 | 8.1.4.2 |

**本机差距**：`sec_pwd_len = 0`（CIS 要求 ≥ 14）是唯一硬差距。锁定策略若为 0 次/永久也应补齐。

---

## 三、本地策略与提权防护

| check id | 本项检查 | CIS | MSS | NIST | 等保三级 |
|---|---|---|---|---|---|
| `sec_uac` | UAC 等级 | **2.3.17.x** UAC 系列（ConsentPromptBehavior / EnableLUA） | ✔ UAC | AC-6 | 8.1.4.2 |
| `sec_guest` | Guest 账户禁用 | **2.3.1.3** Accounts: Guest account status = Disabled | ✔ | AC-2 | 8.1.4.2 |
| `sec_admin_members` | 本地管理员组成员最小化 | **2.3.1.1** Accounts: Administrator account status = Disabled | ✔ | AC-2、AC-6 | 8.1.4.2 |
| `sec_lsa_ppl` | LSA 保护 RunAsPPL | 类别对应 `18.10.x`（LSA Protection） | ✔ Configure LSA protection | SC-39、SI-16 | 8.1.4.4 |
| `sec_wdigest` | WDigest 明文缓存 | **18.3.x** WDigest Authentication = Disabled（本机为何是 18.3.x 而非 2.3.x，见 CIS 版本差异） | ✔ | IA-5、SC-13 | 8.1.4.1 |
| `sec_aie` | AlwaysInstallElevated | **18.x** Windows Installer: Always install with elevated privileges = Disabled | ✔ | CM-7、AC-6 | 8.1.4.4 |
| `sec_appinit` | AppInit_DLLs 注入 | **18.x** AppInit_DLLs 相关 | ✔ | CM-7、SI-7 | 8.1.4.4 |
| `sec_pagefile_clear` | 关机清理页面文件 | **2.3.11.x** Shutdown: Clear virtual memory pagefile = Enabled | ✔ | SC-4、MP-6 | 8.1.4.7 |
| `sec_no_lmhash` | 不存 LM 哈希 | **2.3.11.x** Network security: Do not store LAN Manager hash value on next password change | ✔ | IA-5、SC-13 | 8.1.4.1 |
| `sec_danger_svc` | 危险服务运行状态 | **5.x** System Services 清单 | ✔ | CM-7 | 8.1.4.4 |

---

## 四、网络协议加固

| check id | 本项检查 | CIS | MSS | NIST | 等保三级 |
|---|---|---|---|---|---|
| `sec_smb1` | 禁用 SMBv1 | **18.x** Configure SMB v1 client/server = Disabled | ✔ SMBv1 | CM-7 | 8.1.4.4 |
| `sec_smb_signing` | SMB 服务端强制签名 | **2.3.9.x** Microsoft network server: Digitally sign communications (always) = Enabled | ✔ | **SC-8**、SC-23 | 8.1.3.2 |
| `sec_smb_client_sign` | SMB 客户端强制签名 | **2.3.9.x** Microsoft network client: Digitally sign communications (always) = Enabled | ✔ | SC-8、SC-23 | 8.1.3.2 |
| `sec_ntlm_level` | LAN Manager 认证级别 = NTLMv2 | **2.3.11.7** Network security: LAN Manager authentication level | ✔ | IA-5、SC-13 | 8.1.4.1 |
| `sec_netlogon_sign` | 安全通道签名/加密 | **2.3.9.x** Domain member: Digitally encrypt or sign secure channel data (always) | ✔ | SC-8、SC-23 | 8.1.3.2 |
| `sec_restrict_anon` | 禁止匿名枚举 SAM | **2.3.10.x** Network access: Do not allow anonymous enumeration of SAM accounts | ✔ | AC-3、AC-6 | 8.1.4.2 |
| `sec_anon_sam` | 匿名访问命名管道/共享受限 | **2.3.10.x** Network access: Restrict anonymous access to Named Pipes and Shares | ✔ | AC-3 | 8.1.4.2 |
| `sec_llmnr` | 关闭 LLMNR 多播解析 | **18.10.x** Turn off multicast name resolution（或关闭 LLMNR） | ✔ | CM-7 | 8.1.4.4 |
| `sec_netbios` | 禁用 NetBIOS over TCP/IP | 类别对应 `2.3.11.x` | 无直项 | CM-7 | **8.1.3.5**、8.1.4.4 |
| `sec_winrm` | WinRM 服务暴露 | 类别对应 `18.x` | ✔ | CM-7、AC-17 | 8.1.4.4 |

---

## 五、边界防护与防火墙

| check id | 本项检查 | CIS | MSS | NIST | 等保三级 |
|---|---|---|---|---|---|
| `sec_ports` | 监听端口清单 | 类别对应 `9.x` | 无 | CM-7 | **8.1.3.4**、8.1.4.4 |
| `sec_fw_loose` | 公网宽松入站规则 | **9.1/9.2** Domain/Private profile 默认入站 = Block | ✔ Firewall | **SC-7**、AC-4 | **8.1.3.3**、8.1.3.4 |
| `sec_fw_outbound` | 出站默认动作 | **9.3** Public profile 出站 = Block（CIS 有此要求，但会显著影响可用性） | ✔ | SC-7、AC-4 | 8.1.3.3 |
| `sec_rdp` | RDP 暴露 | **18.10.x** RDP 系列 | ✔ | **AC-17** Remote Access | 8.1.4.4 |
| `sec_rdp_nla` | RDP 强制 NLA | **18.10.x** Require user authentication for remote connections by using Network Level Authentication | ✔ | IA-2、AC-17 | 8.1.4.1 |
| `sec_remote_assist` | 远程协助关闭 | **18.10.x** Configure Offer Remote Assistance = Disabled | ✔ | AC-17 | 8.1.4.4 |
| `sec_remote_assist` / `sec_proxy` | 代理配置 | 无 | 无 | CM-7 | 8.1.3.4 |
| `sec_bluetooth` | 蓝牙开放 | 无直项 | 无 | **AC-18** Wireless Access | 8.1.3.5 |

---

## 六、恶意代码防护与内存保护

| check id | 本项检查 | CIS | MSS | NIST | 等保三级 |
|---|---|---|---|---|---|
| `sec_defender_rt` | 杀软实时保护（含第三方） | **18.10.x** Defender 系列 | ✔ Defender Antivirus | **SI-3** | **8.1.4.5** |
| `sec_asr` | ASR 攻击面缩减规则 | **18.10.x** ASR 规则集 | ✔ ASR | SI-3、CM-7 | 8.1.4.4、8.1.4.5 |
| `sec_cfa` | 受控文件夹访问（防勒索） | **18.10.x** Controlled Folder Access | ✔ | SI-3 | 8.1.4.5 |
| `sec_hvci` | 内核隔离 HVCI | **18.10.x** Turn On Virtualization Based Security | ✔ Device Guard | SC-39、SI-16 | 8.1.4.4 |
| `sec_smartscreen` | SmartScreen | **18.10.x** SmartScreen 系列 | ✔ | SI-3 | 8.1.4.5 |
| `sec_bitlocker` | 系统盘加密 | **18.10.x** BitLocker 系列 | ✔ BitLocker | **SC-28**、MP-6 | **8.1.4.7** 数据保密性 |

---

## 七、审计与日志

| check id | 本项检查 | CIS | MSS | NIST | 等保三级 |
|---|---|---|---|---|---|
| `audit_ps_logging` | PowerShell 脚本块日志 | **18.x** PowerShell Script Block Logging = Enabled | ✔ | **AU-2**、AU-3、AU-12 | **8.1.4.3** |
| `audit_ps_transcript` | PowerShell 转录日志 | **18.x** PowerShell Transcription | ✔ | AU-2、AU-12 | 8.1.4.3 |

> 等保三级 8.1.4.3 对审计有硬要求（覆盖每个用户、记录日期时间/用户/事件类型/结果、日志保护与备份）。
> 本 skill 只查了两条 PowerShell 日志，**离等保 8.1.4.3 的整体要求还差很远**（见第九节缺口）。

---

## 八、启动链与固件可信

| check id | 本项检查 | CIS | MSS | NIST | 等保三级 |
|---|---|---|---|---|---|
| `sec_secureboot` | UEFI Secure Boot | **18.10.x** Secure Boot | ✔ | **SI-7**、SI-16 | **8.1.4.6** 可信验证 |
| `sec_tpm` | TPM 启用 | **18.10.x** TPM 相关 | ✔ | SC-12 | 8.1.4.6 |

---

## 九、无直接基线依据的项（说明它们是"工程判断"）

以下项在四个基线里**找不到逐条对应**，是本 skill 基于威胁情报 / 攻击链 / 工程经验的补充。
**如实告诉用户这一点**，不要包装成"合规要求"。

| 类别 | check id | 依据 |
|---|---|---|
| 未加引号服务路径 | `sec_unquoted_svc` | **MITRE ATT&CK T1574.009**（Unquoted Path）。CIS Win11 未收录此项 |
| 计划任务持久化 | `sec_schtasks` | ATT&CK T1053.005；完整性监控 SI-7 |
| WMI 事件订阅持久化 | `sec_wmi_sub` | ATT&CK T1546.003；SI-7 |
| 启动项签名 | `sec_startup_sig` | ATT&CK T1547.001；SI-7 |
| hosts 文件完整性 | `sec_hosts` | 完整性核对，无基线条款 |
| 内核转储 / 休眠文件 | `stab_dump`、`stab_hiberfil` | 内存镜像含凭据，属 MP-6/SC-4 同类 |
| 网络性能项 | `net_dns`、`net_nic_power`、`net_tcp_autotune` | **纯性能调优，无安全含义** |
| 隐私项 | `priv_telemetry`、`priv_adid`、`priv_bgapps`、`priv_activity`、`priv_tailored`、`priv_location` | 用户隐私偏好。CIS 不涉及；NIST Rev.5 隐私控制已移至隐私框架，不在 800-53 主线 |
| 消费级体验 | `perf_gamedvr`、`perf_powerplan`、`stab_8dot3` | 用户偏好，无基线 |
| 待重启 | `sec_pending_reboot` | 运维状态，无基线 |
| 共享 / 管理员共享 | `sec_shares`、`sec_admin_share` | CIS 2.3.10.x 类别对应（更偏审计） |

---

## 十、本机 vs 基线的实际差距（v9 实跑，2026-10）

| 差距项 | 本机 | 基线要求 | 依据 | 是否阻塞合规 |
|---|---|---|---|---|
| 最小密码长度 | 0 | ≥ 14 | CIS 1.1.4 | **是**（改后强制换密码） |
| 无操作锁屏 | 1800 秒 | ≤ 900 秒 | CIS 2.3.7.x | 是（本机无同室人员，风险已接受） |
| 公网宽松入站规则 | 99 条 Allow Any | Block | CIS 9.1/9.2 | 是（需逐条清理自用程序） |
| NetBIOS | 8/9 网卡已禁用 | 全禁用 | CM-7 | 否（剩 1 张） |
| RDP 启用 | 已启用 | 关闭（如非必需） | AC-17 | 否（用户明确需要手机远控） |
| 审计覆盖 | 仅 PS 两条 | 全类别审计策略 | 等保 8.1.4.3 | **是（当前差最多的一项）** |
| Secure Boot / TPM / BitLocker | 需管理员复测 | 启用 | SI-7 / SC-28 | 未知 |

---

## 十一、基线未覆盖但同样重要的缺口（诚实清单）

本 skill 的 77 项**不等于**一套完整合规基线。以下是明确**没有**覆盖的：

1. **完整审计策略**：CIS 17.x 有 60+ 条高级审计子类别，本 skill 只查 2 条 PowerShell 日志。
2. **用户权限分配（UR）**：CIS 2.3.2.x 一整组（SeDebugPrivilege、SeBackupPrivilege、SeTcbPrivilege 等）未覆盖。
3. **组策略对象（GPO）落地校验**：未做 `gpresult /h` 与基线 diff。
4. **内核与驱动签名强制**：未查驱动签名策略（仅查了启动项签名）。
5. **网络层**：未做端口扫描、未查 IPSec 策略、未查 DNS over HTTPS 状态。
6. **应用层**：未查 Office 宏策略、浏览器策略、Java/.NET 版本。
7. **补丁与漏洞状态**：未查 Windows Update 挂起补丁、未做 CVE 扫描。
8. **凭据卫生深水区**：未查 DPAPI 主密钥、未查 LSA Secrets 残留、未查 kerberos 票据策略。
9. **物理与固件**：未查 BIOS 密码、未查启动顺序锁定、未查 DMA 保护（Thunderbolt DMA）。
10. **入侵检测**：只做了持久化点静态扫描，没有行为监控、没有 Sysmon、没有文件完整性监控（FIM）。

**结论**：本 skill 的定位是**"家用/单机 Windows 的已知攻击面收敛 + 差距可视化"**，不是合规过审工具。
要过等保三级或 CIS 全量加固，需要在上表基础上再做一轮，并且必须承认"没有绝对安全"。
