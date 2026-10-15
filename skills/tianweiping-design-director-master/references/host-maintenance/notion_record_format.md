# Notion 记录格式

每次扫描+应用完成后，把结果写入 Notion，便于回溯历史优化记录。

## 首次使用

1. 用 `notion-search` 搜索关键词：`Windows 优化记录`、`系统体检`、`Security Audit`。
2. 若已存在数据库，直接复用，记下其 database_id。
3. 若不存在，用 `notion-create-database` 在用户指定的父页面下创建，结构见下。
4. **不要**主动创建新数据库。每次先搜索。

## 数据库结构

| 属性名 | 类型 | 说明 |
|---|---|---|
| `Date` | Date | 扫描时间（自动取当前时间） |
| `Host` | Title | 主机名，例如 `DESKTOP-ABC123` |
| `Total` | Number | 检查项总数 |
| `OK` | Number | 通过项数 |
| `Warning` | Number | 警告项数 |
| `Danger` | Number | 危险项数 |
| `Applied` | Multi-select | 本次实际应用的 fix_id 列表 |
| `Status` | Select | `Completed` / `Partial` / `Failed` |
| `Summary` | Rich text | 一句话摘要（例如："修复 5 项警告，2 项危险仍待处理"） |

## 每次记录写什么

### 数据库属性
- `Date`：本次扫描时间
- `Host`：`$env:COMPUTERNAME`
- `Total/OK/Warning/Danger`：来自 scan_health.ps1 输出的 summary
- `Applied`：apply_changes.ps1 返回的 success=true 的 fix_id 列表
- `Status`：
  - `Completed`：所有选定的 fix 都成功
  - `Partial`：部分失败
  - `Failed`：还原点都没建成功
- `Summary`：一句话

### 页面正文（notion-create-pages 的 content）

用 Markdown 写，结构：

```markdown
## 体检摘要
- 扫描时间：{scanned_at}
- 主机：{host}
- 管理员权限：{is_admin}
- 通过 / 警告 / 危险 / 需管理员：{ok} / {warning} / {danger} / {needs_admin}

## 本次已应用
- {fix_id}: 成功/失败 — 消息
- ...

## 仍待处理（warning + danger）
| ID | 类别 | 项目 | 当前值 | 建议 |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## 系统还原点
已创建：{restore_point_message}
```

## 注意

- **不要**把注册表完整 dump 写进去，只写汇总和待处理表。
- 写之前如果 Notion MCP 工具不可用，在最终回复里说明"Notion 记录跳过"，不要因此阻塞本地优化流程。
- 用户没指定父页面时，搜索后直接在搜到的数据库里新增一行；不要新建顶层页面。
