#!/usr/bin/env python3
"""Compile reviewed project declarations into prompts and scoped repair tasks."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from check_project import ManifestError, check_project, sha256


def unique(values):
    return list(dict.fromkeys(values))


def build_handoff(project, base_dir):
    checks = check_project(project, base_dir, "plan")
    if checks["errors"]:
        return {"status": "needs_revision", "errors": checks["errors"], "tasks": [], "repair_queue": []}
    characters = {entry["id"]: entry for entry in project.get("characters", [])}
    assets = {entry["id"]: entry for entry in project.get("assets", [])}
    direction = project.get("direction", {})
    constraints = {entry["id"]: entry for entry in direction.get("constraints", [])}
    profile_verified = checks["capabilities"]["status"] == "declared_verified"
    tasks, repair_queue = [], []
    for item in project["items"]:
        anchors = unique([anchor for key in item.get("characters", []) for anchor in characters[key]["anchors"]])
        locked = [constraints[key]["instruction"] for key in item.get("constraint_ids", [])]
        keep = unique(anchors + direction.get("preserve", []) + locked + item.get("keep", []))
        scene = item.get("scene")
        if scene:
            body = "；".join(scene[field] for field in
                            ("subject", "action", "environment", "composition", "lighting", "style") if field in scene)
        else:
            body = item["prompt"]
        lines = [body.rstrip("。") + "。"]
        if anchors:
            lines.append("角色身份保持：" + "、".join(anchors) + "。")
        if item.get("keep"):
            lines.append("本次保留：" + "、".join(item["keep"]) + "。")
        if direction.get("preserve") or locked:
            lines.append("项目保留要求：" + "；".join(unique(direction.get("preserve", []) + locked)) + "。")
        if direction.get("structural_changes_allowed") is False:
            lines.append("保持结构参考中可见的几何与布局；不要自行改变窗门位置、比例或物体位置。未提供的结构信息保持未知。")
        for ref in item.get("reference_roles", []):
            ordinal = item["references"].index(ref["asset_id"]) + 1
            labels = {"identity": "主体身份", "style": "画风", "composition": "构图", "action": "动作",
                      "first_frame": "首帧状态", "last_frame": "尾帧状态",
                      "structure": "可见结构与布局", "material": "材质与纹理依据", "annotation": "指定修改位置与说明"}
            lines.append(f"参考图{ordinal}用于{labels[ref['role']]}；对应素材{ref['asset_id']}。")
        if "camera" in item:
            camera = item["camera"]
            lines.append("摄影机固定。" if camera["mode"] == "fixed" else f"摄影机运动：{camera['movement']}。")
        generation = item.get("generation", {})
        tasks.append({"item_id": item["id"], "prompt": "\n".join(lines), "keep": keep,
                      "references": [{"id": key, "path": assets[key]["path"], "available": (Path(base_dir) / assets[key]["path"]).is_file()} for key in item.get("references", [])],
                      "editing_frames": item.get("frames"), "trim_in_frame": item.get("trim_in_frame", 0),
                      "execution_parameters": generation.get("parameters", {}) if profile_verified else {},
                      "unverified_parameters": generation.get("parameters", {}) if not profile_verified else {},
                      "generation_mode": generation.get("mode"),
                      "status": "prompt_prepared", "media_created": False})
        failed = [review for review in item.get("reviews", []) if review["result"] == "fail"]
        failed += [dict(review, dimension="design:" + review["dimension"]) for review in item.get("design_reviews", []) if review["result"] == "fail"]
        history = item.get("repair_history", [])
        change_method = len(history) >= 2 and history[-1]["method"] == history[-2]["method"] and all(
            entry["outcome"] == "unchanged" for entry in history[-2:])
        for review in failed:
            priority = "critical" if review["dimension"] in {"brief", "identity", "structure", "text"} else "major"
            source = assets.get(review["asset_id"])
            current_path = (Path(base_dir) / source["path"]).resolve() if source else None
            version_status = "unavailable"
            if current_path and current_path.is_file():
                version_status = "matched" if sha256(current_path) == review["sha256"].lower() else "stale"
            action = ("change_method" if change_method else "localized_repair") if version_status == "matched" else "review_current_version"
            repair_queue.append({"item_id": item["id"], "dimension": review["dimension"],
                                 "priority": priority, "evidence": review["evidence"],
                                 "reviewed_asset_id": review["asset_id"], "reviewed_sha256": review["sha256"],
                                 "keep": keep, "version_status": version_status, "next_action": action,
                                 "already_repaired": False})
    repair_queue.sort(key=lambda entry: (0 if entry["priority"] == "critical" else 1))
    return {"status": "handoff_prepared", "project_id": project["project_id"],
            "direction_brief": direction, "design_direction": checks["design_direction"],
            "tasks": tasks, "repair_queue": repair_queue,
            "required_reviews": checks["required_review_dimensions"], "warnings": checks["warnings"],
            "capabilities": checks["capabilities"],
            "limits": "Prepared text only; no generation or repair executed. Structured declarations are checked, but free-text contradictions and visual consistency still need review. Capability claims do not grant tool access or spending authorization."}


def render_text(report):
    if report["status"] == "needs_revision":
        return "项目数据需要修正：\n" + "\n".join(report["errors"])
    lines = [f"项目：{report['project_id']}", "状态：交接指令已准备；尚未生成或修复媒体。"]
    direction = report.get("direction_brief", {})
    if direction:
        lines += ["", "【创意简报】", "用途：" + direction["purpose"], "受众：" + direction["audience"], "核心表达：" + direction["message"]]
        if direction.get("facts"):
            lines.append("已提供事实：" + "；".join(direction["facts"]))
        if direction.get("assumptions"):
            lines.append("待验证假设：" + "；".join(direction["assumptions"]))
        for deliverable in direction.get("deliverables", []):
            lines.append(f"物料 {deliverable['id']} 对应 {deliverable['item_id']}：{deliverable['purpose']}")
    for task in report["tasks"]:
        lines += ["", f"【{task['item_id']}】", task["prompt"]]
        for ref in task["references"]:
            lines.append(f"素材 {ref['id']}：{ref['path']}" + ("" if ref["available"] else "（文件尚未提供）"))
        if task["editing_frames"] is not None:
            lines.append(f"编辑使用 {task['editing_frames']} 帧，源素材从第 {task['trim_in_frame']} 帧开始。")
        if task["execution_parameters"]:
            lines.append("按已声明能力单独设置参数：" + json.dumps(task["execution_parameters"], ensure_ascii=False, default=str))
        if task["unverified_parameters"]:
            lines.append("待核验参数，暂不提交：" + json.dumps(task["unverified_parameters"], ensure_ascii=False, default=str))
    if report["repair_queue"]:
        lines += ["", "【已有失败项的返修任务】"]
        for repair in report["repair_queue"]:
            lines.append(f"{repair['item_id']} / {repair['dimension']} / {repair['priority']}：{repair['evidence']}；下一步 {repair['next_action']}。")
    lines += ["", "检查维度：" + "、".join(report["required_reviews"]), "限制：" + report["limits"]]
    if report.get("design_direction", {}).get("enabled"):
        lines.append("另需完成12维视觉审稿；不适用项说明理由，未查看项保持未知。")
    if report["warnings"]:
        lines += ["", "待核验："] + report["warnings"]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        project = json.loads(args.manifest.read_text(encoding="utf-8-sig"), parse_float=Decimal)
        report = build_handoff(project, args.manifest.parent)
    except (ManifestError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "invalid_manifest", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str) if args.format == "json" else render_text(report))
    return 1 if report["status"] == "needs_revision" else 0


if __name__ == "__main__":
    raise SystemExit(main())
