---
name: windows-security-network-optimizer
description: Windows 本机白帽级安全审计与加固（79 项检查）。覆盖纵深防御五层：① 家用优化（DNS/UAC/防火墙/遥测/Game DVR/电源计划）；② 凭证与提权（LSA RunAsPPL/WDigest/ClearPageFile/AlwaysInstallElevated/AutoAdminLogon/LimitBlankPwd）；③ 网络协议加固（SMB 签名/NTLMv2/RestrictAnonymous）；④ 持久化与防护（本地管理员审计/AppInit_DLLs/ASR 9 条/受控文件夹/HVCI/SmartScreen）；⑤ 攻击面扫描（未加引号服务路径/宽松入站规则/启动项签名/hosts 劫持/BitLocker）。先扫描出分级报告（OK/Warning/Danger），用户确认后才应用修复，自动创建系统还原点，最后把结果记录到 Notion。当用户说"安全审计"、"查后门"、"查持久化"、"防 Mimikatz"、"防勒索"、"加固 Windows"、"电脑安全体检"、"黑客级安全"、"安全堡垒"时使用。
---

# Windows 白帽安全加固器（堡垒版）

## 核心原则

1. **先扫描后修改**：永远先跑只读扫描，把分级报告交给用户确认，**不要**直接改系统。
2. **可逆优先**：所有写操作前自动创建系统还原点；不删文件、不禁用 Windows 服务。
3. **用户确认**：只应用用户明确勾选的 fix_id。
4. **不碰服务**：本 Skill **不**禁用 SysMain / Print Spooler / Windows Search 等系统服务。
5. **审计为主**：深度项（本地管理员组成员、共享文件夹、未加引号服务路径、外连）默认只**报告**不自动改。
6. **诚实边界**：没有"黑客进不来"的系统。本 skill 收敛已知攻击面，但挡不住 0day、社工、供应链、物理拆盘。把这个边界告诉用户。
7. **Notion 留痕**：每次完成后把记录写入 Notion。

## 工作流

### Step 1：体检扫描

以**管理员**身份打开 PowerShell，运行：

```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\scan_health.ps1"
```

把 stdout 的 JSON 解析出来。脚本输出结构：

```json
{
  "scanned_at": "...",
  "host": "...",
  "is_admin": true,
  "total": 79,
  "ok": 58,
  "warning": 6,
  "danger": 0,
  "needs_admin": 1,
  "duplicates": [],
  "action_count": 5,
  "actions": [ { "fix_id": "...", "name": "...", "status": "warning", "risk": "medium" } ],
  "items": [ { "id":"...", "category":"...", "name":"...", "status":"ok|warning|danger|info|needs_admin", "current":"...", "recommended":"...", "risk":"...", "reversible":true, "description":"...", "fix_id":"..." } ]
}
```

- `actions` 是**已排好序的行动清单**（danger/warning 且有 fix_id，按危险度取前 10），直接拿它跟用户讨论，不用自己再筛。
- `duplicates` 非空说明脚本内部有重复 id，属脚本 bug，要修。
- 全量扫描耗时约 **18–20 秒**（v9 优化后）。若明显变慢，先查是否有人在循环里调 `Get-NetFirewall*Filter`——见 `references/lessons_learned.md` 第 9.1 节。
- **非管理员也能跑出可用结果**：`needs_admin` 的项（Secure Boot/TPM/PSv2 等）标出来即可，不要因为 `is_admin=false` 就拒绝出报告。

**如果 `is_admin=false`**：明确告诉用户"需要管理员 PowerShell 才能完成防火墙/SMBv1/LSA 等深度检查"，建议用管理员身份重开；但非管理员也能跑出 HKCU 部分结果，先展示。

### Step 2：把报告整理给用户

把 items 按 `status=danger` → `warning` → `needs_admin` 排序，用表格展示：

| fix_id | 项目 | 当前 | 建议 | 风险 |
|---|---|---|---|---|

并给出统计："共 N 项，X 通过，Y 警告，Z 危险"。

**推荐修复顺序**（主动告诉用户）：
1. 先修 `risk=high` 的 danger（Defender 裸奔、AppInit_DLLs 被注入、hosts 被劫持）
2. 再修 `risk=high` 的 warning（LSA RunAsPPL、未加引号服务路径、本地管理员组成员审计）
3. 最后修 `risk=low/medium` 的（DNS、遥测、Game DVR、电源计划）

**询问用户**：要应用哪些？让用户回复 fix_id 列表，或说"应用所有 high 风险项"。**不要**自动全选。

### Step 3：确认并执行

用户选定后，先**Dry-run** 一次：

```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\apply_changes.ps1" -FixIds "id1,id2" -WhatIf
```

把 dry-run 结果给用户看一眼，确认无误后**去掉 `-WhatIf`** 正式执行：

```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\apply_changes.ps1" -FixIds "id1,id2"
```

脚本会：
1. 自动 `Enable-ComputerRestore` + `Checkpoint-Computer` 创建还原点
2. 逐个应用 fix
3. 输出 JSON：`{ applied_at, what_if, results: [{fix_id, success, message}] }`

### Step 4：复测

应用完成后，**再跑一次** `scan_health.ps1`，确认刚才的 danger/warning 已经变成 ok。把对比结果告诉用户。

### Step 5：写入 Notion

按 `references/notion_record_format.md` 的格式，用 `notion-operations` MCP 工具记录：

1. 先 `notion-search` 找已有数据库（关键词：`Windows 优化`、`系统体检`、`Security Audit`）
2. 找不到再 `notion-create-database` 新建
3. 用 `notion-create-pages` 新增一行，属性和页面正文按参考文档填

Notion 不可用时跳过这步，在回复里说明即可，不要阻塞主流程。

## 关键文件

- `scripts/scan_health.ps1` — 只读体检，**79 项检查**，输出 JSON，约 18–20 秒
- `scripts/apply_changes.ps1` — 应用修复（49 个 fix 分支），自动建还原点，支持 `-WhatIf`
- `references/optimization_items.md` — 每个 fix_id 的详细说明、注册表路径、回滚方法、风险
- `references/security_playbook.md` — 纵深防御知识体系、MITRE ATT&CK 映射、入侵应急流程
- `references/benchmark_mapping.md` — CIS / Microsoft / NIST / 等保 2.0 基线对照表
- `references/lessons_learned.md` — **本机实跑经验：误报清单、用户红线、已做对项、推荐批次**
- `references/notion_record_format.md` — Notion 数据库 schema 和记录模板

## 改脚本的硬规则（PS 5.1 + 中文 Windows）

1. **编码**：`.ps1` 必须存为 **UTF-8 with BOM**。用 Edit 工具改完会丢 BOM，必须补：

   ```powershell
   $c = [System.IO.File]::ReadAllText($p, [System.Text.UTF8Encoding]::new($false))
   [System.IO.File]::WriteAllText($p, $c, [System.Text.UTF8Encoding]::new($true))
   ```

2. **语法**：PS 5.1 不支持 `??`、三元 `?:`、`-Parallel`。改完用 `[System.Management.Automation.PSParser]::Tokenize(...)` 过一遍。
3. **计数**：`.Count` 在单对象上返回 `$null`，**一律写 `@(...).Count`**。
4. **性能**：禁止在循环里调 `Get-NetFirewall*Filter` / `Get-NetIPsec*Filter` 这类子对象查询——批量拉一次建 `InstanceID` 哈希表，否则单块就能吃 18 秒。
5. **取父目录**：用 `[System.IO.Path]::GetDirectoryName($p)`，不要用 `Split-Path -LiteralPath ... -Parent`（参数集冲突，直接报错）。
6. **改完必须实跑计时**，确认没引入新误报（尤其 `danger` 数不该无故上升）。
7. 追加文档用**单引号** here-string `@'...'@`，用 `@"..."@` 会把 `$变量` 展开写坏内容。

以上每条都对应 `references/lessons_learned.md` 第九节的一个真实踩坑记录，改脚本前先读那一节。

## 工作流前置：先读经验文档

**开始任何扫描/修复前**，先读 `references/lessons_learned.md`。里面有：
- 这台机器的真实画像（杀软、RDP、游戏、网络环境）
- 已知误报（哪些"danger/warning"其实是正常的）
- 用户红线（不要碰什么）
- 已经做对的项（不用重复建议）
- 推荐修复批次（低风险高收益组合）

读了之后，把扫描结果里命中"已知误报"的项**过滤掉再展示给用户**，不要重复报警。

## 安全红线

- **不要**禁用任何 Windows 服务（`sc config ... start=disabled`、`Stop-Service`）。
- **不要**删文件、删驱动、删注册表项。
- **不要**改组策略里的密码复杂度、锁屏时间（用户没要求）。
- **不要**一键全选所有 fix 自动执行——必须让用户确认。
- **不要**跳过还原点创建。如果还原点失败，在执行前再次跟用户确认。
- 涉及 `sec_uac_enable`、`sec_smb1_disable`、`sec_ports_block`、`sec_asr_enable`、`sec_hosts_reset` 这类中高风险项，dry-run 后要单独提醒一次。
- **不要**自动删本地管理员组成员——只报告，让用户自己判断。
- **不要**自动清 hosts 文件——先备份再改。

## 常见问题

- **脚本被执行策略拦截**：加 `-ExecutionPolicy Bypass`（已在上面命令里）。
- **`Set-DnsClientServerAddress` 报权限错**：说明没在管理员 PowerShell 里跑。
- **UAC 修改后不生效**：需要重启或注销。
- **SMBv1 禁用后老 NAS 连不上**：按 `references/optimization_items.md` 里的回滚命令恢复。
- **启用 ASR 后某个常用软件被拦**：去 Windows 安全中心 → 病毒和威胁防护 → 勒索软件防护 → 允许应用通过受控文件夹，加白名单。
- **HVCI 开了之后某个老驱动蓝屏**：在 Windows 安全中心 → 设备安全性 → 内核隔离里关掉，这是已知兼容性问题。

