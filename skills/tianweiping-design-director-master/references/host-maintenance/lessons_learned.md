# 实跑经验与本机画像

这份文档记录在 **SEVEN 这台 RTX 5080 家用机**上反复实跑积累的经验。以后扫描/修复时先读这里，避免重复判断和误报。

---

## 一、本机硬件与软件画像

- **主机名**：SEVEN
- **OS**：Windows 11 家用/专业版
- **硬件**：RTX 5080 台式机，32GB+ 内存
- **杀软**：腾讯电脑管家（QQPCMgr）——不是 Windows Defender
- **远程访问**：RDP 已启用，用户用手机远程控制。**不要关 RDP**，但必须确认 NLA 已开
- **游戏**：Dota 2、PUBG（吃鸡），装了 ACE 反作弊（AntiCheatExpert）
- **网络**：家里 192.168.x，双网卡（以太网 + WLAN）
- **物理环境**：用户一个人住/用，没人接触电脑。锁屏可以放宽到 30 分钟

## 二、已经"误报"的检查项（看到这些别大惊小怪）

### 1. Defender 实时保护关闭 = 误报
- **现象**：`sec_defender_rt` 报 danger "已关闭且无第三方杀软"
- **真相**：用户装了腾讯电脑管家，Defender 自动让位。**这是正常的，不要建议开启 Defender**，会冲突。
- **修复方法**：扫描时先查 Security Center 注册表看有没有第三方杀软，有就不报 danger。

### 2. 端口监听 0.0.0.0 = 不一定危险
- **现象**：`netstat` 看到一堆 0.0.0.0:端口 LISTENING
- **真相**：用户防火墙开着，这些端口外网根本连不进来。要结合防火墙状态一起判断。
- **规则**：防火墙启用时，本地监听端口只报 info，不报 danger。

### 3. 125 条公网 Allow Any 防火墙规则 = 游戏/腾讯软件加的
- **现象**：`sec_fw_loose` 报 warning "125 条 Allow Any"
- **真相**：全是腾讯系软件、ACE 反作弊、P2P 下载、游戏对战加的。**不要自动删**，删了游戏/加速器断网。
- **处理**：只报告，让用户自己看。

### 4. 13 个未加引号服务路径 = ACE 反作弊 + 腾讯
- **现象**：`sec_unquoted_svc` 报 warning
- **真相**：路径是 `C:\Program Files (x86)\Tencent\QQPCMgr\...` 和 `C:\Program Files\AntiCheatExpert\...`。这些是**合法软件**，不是攻击者。
- **处理**：只报告，不要"修复"（你也修不了，人家自己装的）。

### 5. Game DVR = 1
- **现象**：`perf_gamedvr` 报 warning
- **真相**：用户玩游戏，Game DVR 后台录制会掉帧。这个**确实该关**，是真问题。

## 三、用户明确不要动的东西

1. **不要禁用 Windows 系统服务**：SysMain、Print Spooler、Windows Search、Telnet 等都不碰。
2. **不要自动删本地管理员组成员**：只报告。
3. **不要自动清 hosts 文件**：先备份再动。
4. **不要关 RDP**：用户手机远程要用。
5. **不要一键全选所有 fix 自动跑**：必须让用户确认。
6. **锁屏 30 分钟就够**：用户一个人住，不要建议 5 分钟。
7. **不要开 Defender**：会和腾讯电脑管家打架。
8. **不要强推 14 位密码策略**：先问用户当前密码够不够长，再决定跑不跑 sec_pwd_hardening。

## 四、实跑确认本机已经做对的

这些项在 SEVEN 上已经是 ok，不用再建议：

- RDP NLA 已开（UserAuthentication=1）
- Netlogon 安全通道签名已开
- 匿名 SAM 枚举已禁止
- 不存 LM hash
- 账户锁定阈值 10 次
- SMBv1 已禁用
- 三个防火墙 profile 都启用
- HVCI（内存完整性）已开
- UAC 已开（ConsentPromptBehaviorAdmin=5，默认值）

## 五、用户偏好与沟通方式

- **执行型，不要理论**：直接给 fix_id 列表和命令，不要讲大道理。
- **风险敏感但能接受可逆操作**：所有写操作前自动建还原点就行，不用每步问。
- **价格敏感**：优先免费方案。
- **中文回复**：所有输出中文。

## 六、PowerShell 脚本踩坑记录

1. **PS 5.1 必须 UTF-8 with BOM**：用 `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($true))` 重存。否则中文乱码导致解析失败。
2. **PS 5.1 不支持 `??` 运算符**：用 if/else 替代。
3. **`net accounts` 输出中英双语**：正则要同时匹配中英文（`'最小密码长度|Minimum password length'`）。
4. **`auditpol /get` 输出本地化**：判断时要匹配中文 "成功和失败" 和英文 "Success and Failure"。
5. **HKCU 不需要管理员**：屏保、遥测、后台应用这些 HKCU 项非管理员也能跑；HKLM 才需要提权。
6. **`Get-NetFirewallProfile` 需要管理员**：非管理员跑会报错，要 catch。

## 七、推荐修复批次（在 SEVEN 上安全）

低风险高收益，可批量跑：

```
sec_lsa_ppl_enable,
sec_wdigest_disable,
sec_pagefile_clear_on,
sec_limit_blank_enable,
sec_aie_disable,
sec_restrict_anon_set,
sec_lock_set,
priv_telemetry_min,
priv_bgapps_off,
priv_activity_off,
perf_gamedvr_off,
sec_smartscreen_on,
dev_ps_remotesigned,
stab_autoreboot_off,
stab_dump_set,
sec_netbios_off,
sec_smb_client_sign_on,
audit_ps_logging_on,
sec_llmnr_off
```

中风险（可能影响功能，单独问用户）：

```
sec_uac_max,           # 会多弹窗
sec_rdp_harden,        # 已经 ok，跳过
sec_hvci_enable,       # 已经 ok，跳过
sec_asr_enable,        # 可能误拦游戏/破解软件
sec_cfa_enable,        # 会弹窗要放行
sec_pwd_hardening,     # 强制 14 位密码
```

不要跑：

```
sec_defender_enable,   # 装了腾讯电脑管家
sec_rdp_disable,       # 用户要用 RDP
sec_hosts_reset,       # hosts 干净
sec_ports_block,       # 防火墙已经开了
```

### 6. WMI "SCM Event Log Filter" = 合法 Windows
- **现象**：sec_wmi_sub 报 warning "发现: SCM Event Log Filter"
- **真相**：这是 Windows 自带的服务控制管理器事件日志过滤器，不是后门。
- **规则**：WMI 订阅里出现 SCM / Windows Update / Microsoft / Defender 字样就是系统自带，不报 warning。只有随机 GUID 名 / PowerShell 命令 / wmic 调用才真可疑。

### 7. sec_psv2 非管理员读不到
- **现象**：非管理员跑 Get-WindowsOptionalFeature 返回空
- **真相**：这个 cmdlet 需要管理员。非管理员时 info "无法读取" 正常。

### 8. 管理员共享 (ADMIN$/C$) 是默认
- **现象**：sec_admin_share 报 ADMIN$, C$, D$, E$, F$, IPC$
- **真相**：Windows 默认隐藏管理共享，远程访问需管理员凭证。防火墙开着就没事，报 info 即可。

### 9. 凭据管理器有 6 条凭据
- **现象**：sec_cred_vault 报 6 条已存凭据
- **真相**：用户自己存的网络/网站密码。报 info 提醒审查即可，不要建议清空。

### 10. 本地代理 127.0.0.1:7993 = 用户自己的 VPN
- **现象**：sec_proxy 报 "已设: 127.0.0.1:7993"
- **真相**：用户用 Clash/V2Ray 类代理客户端，端口 7890/7993 是常见本地代理端口。这是合法的。
- **规则**：代理地址是 127.0.0.1 / localhost 开头的 = 用户自己的代理软件，报 info 不警告。只有代理指向外部陌生 IP 才需要警惕。

### 11. Secure Boot / TPM 非管理员读不到
- **现象**：非管理员跑 Confirm-SecureBootUEFI / Get-Tpm 返回空
- **真相**：这些 cmdlet 需要管理员。非管理员时 info 是正常的。

### 12. OpenSSH / IIS / SQL Server 都未运行
- **现象**：sec_ssh_server / sec_iis / sec_sql 全是 ok
- **真相**：家用机没跑这些服务，正常。如果哪天跑了，说明用户在搭服务器，那时候才需要关注。

---

# 九、v9 优化轮：误报根因 + 性能瓶颈（重要，改脚本前必读）

这一轮把扫描从 64 秒压到 ~18 秒、warning 从 25 条压到 6 条。以下都是踩过的真坑。

## 9.1 性能：逐条查防火墙过滤器是最大瓶颈

- **现象**：整轮扫描 64 秒。
- **根因**：`Get-NetFirewallRule | ForEach-Object { $_ | Get-NetFirewallAddressFilter }` —— 逐条查过滤器是 O(n) 次 RPC 往返，200 条规则实测 18.3 秒；应用过滤器再来一遍又是 18 秒。
- **正解**：批量加载一次建哈希表，用 `InstanceID` 关联：

```powershell
$afMap = @{}
foreach ($x in (Get-NetFirewallAddressFilter)) { $afMap[$x.InstanceID] = $x }
$apMap = @{}
foreach ($x in (Get-NetFirewallApplicationFilter)) { $apMap[$x.InstanceID] = $x }
# 用时：$afMap[$rule.InstanceID]
```

实测 0.1s + 0.2s。**凡是 `Get-NetFirewall*Filter`、`Get-NetIPsec*Filter` 这类子对象查询，一律批量加载后按 InstanceID 索引，禁止在循环里调。**

## 9.2 Split-Path -LiteralPath 不支持 -Parent，会直接报错

- **现象**：整块 try 抛「无法使用指定的命名参数解析参数集」，结果降级成「无法枚举」。
- **根因**：`Split-Path` 的 `-LiteralPath` 属于 LiteralPathSet，**不支持 `-Parent`**（`-Parent` 只在 Path 参数集里）。
- **正解**：取父目录用 .NET：

```powershell
$parent = [System.IO.Path]::GetDirectoryName($prefix)
```

路径含中文/特殊字符时也不会有歧义。

## 9.3 第三方杀软检测：注册表路径在 Win11 不存在

- **现象**：装了腾讯电脑管家却检测不到，Defender 被误报成 danger。
- **根因**：`HKLM:\SOFTWARE\Microsoft\Security Center\Provider\Av` 在 Win11 上不存在（`Test-Path` 返回 False）。
- **正解**：用 WMI，非管理员也能读：

```powershell
Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct |
  Select-Object displayName
```

实测返回「腾讯电脑管家系统防护」+「Windows Defender」，过滤掉 Defender 即得第三方杀软。注册表只作兜底。

## 9.4 C:\ 根目录 ACL 只给 AppendData，不能当成可写

- **现象**：加了 ACL 判定后，5 个服务被误报成「可劫持 → C:\Program」。
- **根因**：`C:\` 默认给 `Authenticated Users: AppendData`，这是**建子目录**权限，不是**建文件**权限。要劫持 `C:\Program.exe` 必须能建文件。
- **正解**：只认建文件权限，用位运算判：

```powershell
$bits = [int64]$ace.FileSystemRights
$canCreateFile = (($bits -band 0x2) -ne 0) -or
                 ($ace.FileSystemRights.ToString() -match 'FullControl|Modify|\bWrite\b')
```

`0x2` 是 WriteData/AddFile；AppendData 是 `0x4`，**必须排除**，否则 C:\ 会被判成可写、全盘误报。

- **旁证**：干净系统上「含空格未加引号服务路径」实测有 **263 个**，全部在 Program Files 下、中间目录不可写 → 全是正常的。早先报的「13 个可疑」纯属误报。

## 9.5 PowerShell 执行策略：千万别看 Process 作用域

- **现象**：`LocalMachine=RemoteSigned`（本来就是对的值），却报 warning。
- **两个根因**：
  1. 原逻辑是「任一作用域为 Undefined 就警告」，而 `CurrentUser=Undefined` 是出厂默认，必然误报。
  2. 改成按 Process 优先解析后，又读到 `Process=Bypass` —— 那是**扫描器自己用 `-ExecutionPolicy Bypass` 启动带进来的**，不代表系统配置。
- **正解**：按 `CurrentUser → LocalMachine → UserPolicy → MachinePolicy` 取第一个非 Undefined 作为生效值，**明确跳过 Process**。生效值为 RemoteSigned / AllSigned 判 ok；Unrestricted / Bypass 判 warning。

## 9.6 非管理员是常态，别让「需要提权」污染结果

- 用户态下必然失败的调用：`Get-WindowsOptionalFeature`（抛 requires elevation）、`Confirm-SecureBootUEFI`、`Get-Tpm`、部分 `Get-NetFirewallProfile`。
- `Get-WindowsOptionalFeature` 失败很慢（先建 COM 连接再失败）。**必须先判 `$isAdmin` 再决定调不调**，非管理员直接给 needs_admin，不要硬调。
- 结论：脚本要能在**非管理员下依然跑出可用结果**，并在报告里标明哪些项需要提权复测。

## 9.7 统计与输出层的坑

- `($x | Where-Object {...}).Count` 在**零匹配**时返回 `$null`（不是 0），JSON 里会变成 `null`，前端算数就崩。**一律写 `@(...).Count`。**
- 报告别只给数字。99 条 Allow Any 没有意义，**按程序归组**（coze.exe×10 / TxBugReport.exe×4 / PlayGTAV.exe×4 …）才能让人判断该留哪条。
- 输出前做一次 `Group-Object id` 去重，并在 JSON 里暴露 `duplicates` 字段，防止后续加检查项时撞 id。

## 9.8 本机当前基线（v9 实跑，非管理员，2026-10）

```
total=79  ok=58  warning=6  danger=0  needs_admin=1  耗时 ≈18-20s
```

剩余 6 条 warning，**全部是真实项，不是误报**：

| id | 当前 | 处理建议 |
|---|---|---|
| sec_rdp | 已启用 | 用户要用手机远控，保留 |
| priv_bgapps | 后台应用允许运行 | 可关，低优先 |
| sec_fw_loose | 99 条公网 Allow Any | 已按程序归组，看陌生程序再禁 |
| sec_netbios | 8/9 网卡已禁用 | 已加固，剩 1 张 |
| sec_danger_svc | SessionEnv / TermService | RDP 依赖，保留 |
| sec_pwd_len | 最小密码长度 0 | CIS 建议 14，改了会强制换密码 |

对比 v8：NetBIOS 从 0/11 → 8/9 已禁用，说明 `sec_netbios_off` 已实际生效。

## 9.9 改脚本后的必做验证

1. `[System.Management.Automation.PSParser]::Tokenize` 过一遍语法（PS 5.1 无 `-Parallel`）。
2. **重新写入 UTF-8 with BOM**：`[System.IO.File]::WriteAllText($p, $c, [System.Text.UTF8Encoding]::new($true))`。Edit 工具会丢掉 BOM，改完必须补。
3. 实跑一次并计时，确认没引入新的误报（尤其 danger 数不该无故上升）。
4. **追加文档时用单引号 here-string `@'...'@`**，不要用 `@"..."@` —— 后者会把 `$变量`、反引号全部展开，把代码示例写坏（本轮已踩过一次）。
