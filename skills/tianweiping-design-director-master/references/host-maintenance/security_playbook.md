# Windows 安全堡垒知识手册

> 这不是玄学，是分层防御。没有"黑客进不来"的系统，只有"让入侵代价远超收益"的系统。
> 本手册把扫描脚本里的每一项映射到真实攻击链，告诉你为什么要做、被打穿了怎么发现、怎么应急。

## 目录

- [纵深防御的五层模型](#纵深防御的五层模型)
- [你的机器面对的真实威胁](#你的机器面对的真实威胁)
- [按 MITRE ATT&CK 映射](#按-mitre-attack-映射)
- [入侵后应急 checklist](#入侵后应急-checklist)
- [日常习惯（比任何脚本都重要）](#日常习惯比任何脚本都重要)

---

## 纵深防御的五层模型

| 层 | 目标 | 对应本 skill 的检查 |
|---|---|---|
| **1. 物理** | 别人拿到你硬盘/笔记本读不到数据 | BitLocker、锁屏密码、自动锁屏 |
| **2. 身份** | 拿到一个密码不等于拿到全部 | UAC、LSA RunAsPPL、WDigest 禁用、凭据不落地 |
| **3. 网络** | 外面打不进来，进来了出不去 | 防火墙 profile、SMB 签名、NTLMv2、危险端口、空会话 |
| **4. 执行** | 恶意代码跑不起来 | SmartScreen、ASR、受控文件夹、Defender、HVCI、驱动签名 |
| **5. 持久化** | 跑起来了也留不下来 | 启动项签名、AppInit_DLLs、服务路径、管理员组审计 |

任何单层被突破，其他层还能挡。这就是为什么这个 skill 检查 50 项而不是 1 项。

---

## 你的机器面对的真实威胁

按概率从高到低（不是电影里那种国家级黑客）：

1. **破解软件/外挂带毒**（你装游戏修改器、激活工具时）→ ASR、Defender、SmartScreen 挡
2. **钓鱼邮件/IM 附件**（微信 QQ 收到"发票.exe"）→ ASR（Office 宏拦截）、受控文件夹
3. **浏览器 0day / 恶意广告** → SmartScreen、浏览器自动更新、HVCI
4. **WiFi 嗅探/中间人**（咖啡厅酒店）→ SMB 签名、HTTPS、不自动连开放 WiFi
5. **熟人/室友物理接触** → BitLocker、自动锁屏、BIOS 密码（本 skill 不覆盖）
6. **供应链投毒**（npm/pip 包被黑）→ 这层本 skill 挡不住，靠锁版本+审查
7. **0day RCE** → 这层挡不住，靠打补丁（sec_pending_reboot）

---

## 按 MITRE ATT&CK 映射

本 skill 检查项对应的攻击技术编号：

| ATT&CK 技术 | 名字 | 本 skill 对应检查 |
|---|---|---|
| T1003 | OS 凭据 dump (Mimikatz) | sec_lsa_ppl, sec_wdigest |
| T1021.002 | SMB/Windows Admin Shares 横向 | sec_smb_signing, sec_smb1 |
| T1021.001 | RDP 横向 | sec_rdp |
| T1047 | WMI 命令执行 | sec_asr (WMI event 持久化拦截) |
| T1053 | 计划任务持久化 | sec_startup_sig（扩展） |
| T1059.001 | PowerShell | dev_ps_exec |
| T1068 | 提权（未加引号服务路径） | sec_unquoted_svc |
| T1071 | 命令与控制 (C2) | sec_fw_loose、外连审计（扩展） |
| T1112 | 修改注册表 | 本 skill 自身就在做，但也监控 AppInit/IFEO |
| T1134 | 访问令牌操纵 | sec_lsa_ppl |
| T1197 | BITS  jobs 持久化 | 本 skill 未覆盖（高级） |
| T1204.002 | 用户执行恶意文件 | sec_smartscreen, sec_asr |
| T1210 | 利用 SMB 中继 | sec_smb_signing |
| T1505.003 | Web Shell（不适用你本机） | — |
| T1547.001 | 注册表运行项持久化 | sec_startup_sig |
| T1547.010 | AppInit DLLs | sec_appinit |
| T1548 | 提权（AlwaysInstallElevated） | sec_aie |
| T1562.001 | 禁用安全工具 | sec_defender_rt |
| T1486 | 数据加密勒索 | sec_cfa（受控文件夹） |

---

## 入侵后应急 checklist

如果你怀疑已经被入侵（不是日常扫描，是真实怀疑）：

1. **拔网线**（物理断网，不要关机，内存里有证据）
2. **不要登录敏感账户**（银行、邮箱）——用另一台干净的机器改密码
3. **记录当前状态**：
   - `Get-Process | Sort-Object CPU -Descending | Select -First 20`
   - `Get-NetTCPConnection -State Established | Select LocalAddress,LocalPort,RemoteAddress,RemotePort,OwningProcess`
   - `Get-LocalUser | Where-Object {$_.Enabled}`
   - `Get-LocalGroupMember Administrators`
4. **断网后跑一次本 skill 的扫描**，把报告留存
5. **从干净介质重装系统**——这是唯一 100% 可靠的清除方法。不要相信杀毒软件"清除成功"。
6. **改所有密码**（邮箱、GitHub、银行、浏览器保存的密码），开 2FA
7. **检查账号异地登录**：微信、QQ、邮箱、云盘、游戏账号

---

## 日常习惯（比任何脚本都重要）

1. **不用管理员账户日常上网**。建一个标准账户，需要时再 UAC 提权。这一条挡掉 80% 自动提权 malware。
2. **破解软件/外挂/激活工具是最大风险源**。不是 skill 不行，是这种东西本身就带毒。
3. **浏览器自动更新别关**，Office/Windows 补丁别拖。
4. **重要文件本地+云双备份**（3-2-1 原则：3 份副本、2 种介质、1 份离线）。勒索软件打穿了你还有备份。
5. **密码管理器 + 唯一密码 + 2FA**。1Password / Bitwarden。一个密码泄露等于全部泄露。
6. **可疑 U 盘不插**。
7. **定期看一眼任务管理器和开机启动项**，比什么扫描都早发现异常。

---

## 这个 skill 挡不住什么（诚实清单）

- **0day 漏洞**：厂商还没出补丁的漏洞，谁也挡不住。
- **你自己被骗**：钓鱼邮件里你主动点了"允许"，UAC 你自己点了"是"。
- **供应链攻击**：你 `npm install` 的包被作者账号黑了。
- **物理拆除硬盘**：没 BitLocker 就谁都能读。
- **带键盘记录器的恶意驱动**：HVCI 能挡未签名的，但签名过的恶意驱动挡不住。

承认这些边界，才是真安全。
