#!/usr/bin/env python3
"""Read-only manifest checks. No generation, network, or media-quality inference."""

import argparse
import hashlib
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path


class ManifestError(ValueError):
    pass


def obj(value, name):
    if not isinstance(value, dict):
        raise ManifestError(f"{name} must be an object")
    return value


def sequence(value, name):
    if not isinstance(value, list):
        raise ManifestError(f"{name} must be an array")
    return value


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ManifestError(f"{name} must be an integer >= {minimum}")
    return value


def string(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{name} must be a nonempty string")
    return value


def boolean(value, name):
    if type(value) is not bool:
        raise ManifestError(f"{name} must be a boolean")
    return value


def strings(value, name):
    return [string(v, f"{name}[{i}]") for i, v in enumerate(sequence(value, name))]


def numeric(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ManifestError(f"{name} must be a finite decimal")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ManifestError(f"{name} is not a decimal") from exc
    if not result.is_finite():
        raise ManifestError(f"{name} must be finite")
    return result


def amount(value, name):
    result = numeric(value, name)
    if result < 0:
        raise ManifestError(f"{name} must be nonnegative")
    return result


def indexed(value, name):
    records = {}
    for i, entry in enumerate(sequence(value, name)):
        entry = obj(entry, f"{name}[{i}]")
        key = string(entry.get("id"), f"{name}[{i}].id")
        if key in records:
            raise ManifestError(f"duplicate {name} id: {key}")
        records[key] = entry
    return records


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_production_rules(project, items, assets, errors, warnings):
    """Check explicit declarations, not semantic claims hidden in free text."""
    capability = project.get("capabilities")
    verified = False
    if capability is not None:
        capability = obj(capability, "capabilities")
        string(capability.get("entry"), "capabilities.entry")
        string(capability.get("model"), "capabilities.model")
        if capability.get("status") not in {"verified", "unknown"}:
            raise ManifestError("capabilities.status must be verified or unknown")
        verified = capability["status"] == "verified"
        if verified:
            string(capability.get("source"), "capabilities.source")
            try:
                date.fromisoformat(string(capability.get("checked_on"), "capabilities.checked_on"))
            except ValueError as exc:
                raise ManifestError("capabilities.checked_on must be YYYY-MM-DD") from exc
        modes = strings(capability.get("modes", []), "capabilities.modes")
        descriptors = obj(capability.get("parameters", {}), "capabilities.parameters")
    else:
        modes, descriptors = [], {}
    for key, item in items.items():
        scene = obj(item.get("scene", {}), f"item {key}.scene")
        for field, value in scene.items():
            if field not in {"subject", "action", "environment", "composition", "lighting", "style"}:
                raise ManifestError(f"unknown structured scene field: {field}")
            string(value, f"item {key}.scene.{field}")
        camera = item.get("camera")
        if camera is not None:
            camera = obj(camera, f"item {key}.camera")
            mode = camera.get("mode")
            movement = string(camera.get("movement"), f"item {key}.camera.movement")
            if mode not in {"fixed", "moving"}:
                raise ManifestError("camera.mode must be fixed or moving")
            if (mode == "fixed" and movement != "none") or (mode == "moving" and movement == "none"):
                errors.append(f"item {key}: camera mode conflicts with declared movement")
        roles = sequence(item.get("reference_roles", []), f"item {key}.reference_roles")
        seen_roles = set()
        for role in roles:
            role = obj(role, "reference role")
            ref = string(role.get("asset_id"), "reference role.asset_id")
            if ref not in assets or ref not in item.get("references", []):
                errors.append(f"item {key}: reference role uses an unbound asset {ref}")
            role_name = role.get("role")
            if role_name not in {"identity", "style", "composition", "action", "first_frame", "last_frame", "structure", "material", "annotation"}:
                raise ManifestError("unknown reference role")
            if (ref, role_name) in seen_roles:
                errors.append(f"item {key}: duplicate reference role")
            seen_roles.add((ref, role_name))
        generation = item.get("generation")
        if generation is not None:
            generation = obj(generation, f"item {key}.generation")
            mode = string(generation.get("mode"), f"item {key}.generation.mode")
            params = obj(generation.get("parameters", {}), f"item {key}.generation.parameters")
            if not verified:
                warnings.append(f"item {key}: generation mode and parameters await capability verification")
            else:
                if mode not in modes:
                    errors.append(f"item {key}: unsupported generation mode {mode}")
                for param, value in params.items():
                    if param not in descriptors:
                        errors.append(f"item {key}: unsupported generation parameter {param}")
                        continue
                    descriptor = obj(descriptors[param], f"parameter {param}")
                    value_type = descriptor.get("type")
                    validators = {"string": lambda v: isinstance(v, str),
                                  "integer": lambda v: type(v) is int,
                                  "number": lambda v: type(v) in {int, float, Decimal},
                                  "boolean": lambda v: type(v) is bool}
                    if value_type not in validators:
                        raise ManifestError(f"invalid declared parameter type: {param}")
                    if not validators[value_type](value):
                        errors.append(f"item {key}: wrong type for generation parameter {param}")
                        continue
                    if "choices" in descriptor:
                        choices = sequence(descriptor["choices"], f"parameter {param}.choices")
                        if value not in choices:
                            errors.append(f"item {key}: disallowed value for generation parameter {param}")
                    if value_type in {"integer", "number"}:
                        number = numeric(value, f"generation parameter {param}")
                        if "min" in descriptor and number < numeric(descriptor["min"], f"{param}.min"):
                            errors.append(f"item {key}: generation parameter {param} below declared minimum")
                        if "max" in descriptor and number > numeric(descriptor["max"], f"{param}.max"):
                            errors.append(f"item {key}: generation parameter {param} above declared maximum")
        history = sequence(item.get("repair_history", []), f"item {key}.repair_history")
        for entry in history:
            entry = obj(entry, "repair history entry")
            string(entry.get("method"), "repair method")
            if entry.get("outcome") not in {"improved", "unchanged", "unknown"}:
                raise ManifestError("repair outcome must be improved, unchanged or unknown")
            before = string(entry.get("before_asset_id"), "repair before_asset_id")
            after = string(entry.get("after_asset_id"), "repair after_asset_id")
            if before == after or before not in assets or after not in assets:
                errors.append(f"item {key}: repair history needs distinct, known before/after assets")
        integer(item.get("trim_in_frame", 0), f"item {key}.trim_in_frame")
        boolean(item.get("exact_output_frames", False), f"item {key}.exact_output_frames")
    return {"status": "declared_verified" if verified else "unknown",
            "limits": "Checks the declared capability profile only; source accuracy and current account access must be independently verified."}


DESIGN_DIMENSIONS = ("concept", "layout", "color", "typography", "negative_space", "material",
                     "perspective", "lighting", "series_consistency", "finish", "information", "cultural_context")


def check_design_direction(project, items, assets, measured, stage, errors, warnings, pending):
    direction = project.get("direction")
    enabled = direction is not None or any(any(field in item for field in ("design_reviews", "constraint_ids", "planned_changes")) for item in items.values())
    if not enabled:
        return {"enabled": False, "checks": []}
    direction = obj(direction if direction is not None else {}, "direction")
    if direction:
        for field in ("purpose", "audience", "message"):
            string(direction.get(field), f"direction.{field}")
        if direction.get("task") not in {"architecture", "interior", "poster", "illustration", "character", "video", "other"}:
            raise ManifestError("unknown direction.task")
        strings(direction.get("facts", []), "direction.facts")
        strings(direction.get("assumptions", []), "direction.assumptions")
        strings(direction.get("preserve", []), "direction.preserve")
    change_allowed = direction.get("structural_changes_allowed")
    if change_allowed is not None:
        boolean(change_allowed, "direction.structural_changes_allowed")
    constraints = indexed(direction.get("constraints", []), "direction.constraints")
    for key, constraint in constraints.items():
        source = string(constraint.get("source_asset_id"), f"constraint {key}.source_asset_id")
        string(constraint.get("instruction"), f"constraint {key}.instruction")
        if source not in assets:
            errors.append(f"constraint {key}: unknown source asset {source}")
    deliverables = indexed(direction.get("deliverables", []), "direction.deliverables")
    for key, deliverable in deliverables.items():
        target = string(deliverable.get("item_id"), f"deliverable {key}.item_id")
        string(deliverable.get("purpose"), f"deliverable {key}.purpose")
        if target not in items:
            errors.append(f"deliverable {key}: unknown item {target}")
    checked = []
    for key, item in items.items():
        for constraint_id in strings(item.get("constraint_ids", []), f"item {key}.constraint_ids"):
            if constraint_id not in constraints:
                errors.append(f"item {key}: unknown preservation constraint {constraint_id}")
            elif constraints[constraint_id]["source_asset_id"] not in item.get("references", []):
                errors.append(f"item {key}: preservation constraint source is not bound to this item")
        for change in sequence(item.get("planned_changes", []), f"item {key}.planned_changes"):
            change = obj(change, "planned change")
            category = string(change.get("category"), "planned change.category")
            if category not in {"geometry", "material", "lighting", "camera", "composition", "text", "props", "identity"}:
                raise ManifestError("unknown planned change category")
            string(change.get("target"), "planned change.target")
            if category == "geometry" and change_allowed is False:
                errors.append(f"item {key}: planned geometry change conflicts with the preservation brief")
        seen = set()
        for review in sequence(item.get("design_reviews", []), f"item {key}.design_reviews"):
            review = obj(review, "design review")
            dimension = string(review.get("dimension"), "design review.dimension")
            if dimension not in DESIGN_DIMENSIONS or dimension in seen:
                raise ManifestError(f"item {key}: unknown or duplicate design review dimension {dimension}")
            seen.add(dimension)
            result = review.get("result")
            if result not in {"pass", "fail", "unknown", "na"}:
                raise ManifestError("design review.result must be pass/fail/unknown/na")
            if result == "na":
                string(review.get("reason"), "design review.reason")
                if dimension == "typography" and project.get("text_required", False):
                    errors.append(f"item {key}: typography cannot be excluded when text is required")
            if result in {"pass", "fail"}:
                for field in ("evidence", "reviewer", "method", "asset_id", "sha256"):
                    string(review.get(field), f"design review.{field}")
                if review["method"] not in {"image_view", "video_playback", "user_review"}:
                    errors.append(f"item {key}: design review needs visual evidence rather than file metadata")
                if review["asset_id"] != item.get("output_asset_id"):
                    errors.append(f"item {key}: design review is not bound to the output asset")
                if stage == "delivery":
                    actual = measured.get(review["asset_id"])
                    if not actual or review["sha256"].lower() != actual["sha256"]:
                        errors.append(f"item {key}: stale or unverifiable design {dimension} review")
                    if result == "fail":
                        errors.append(f"item {key}: design {dimension} review failed")
            if stage == "delivery" and result == "unknown":
                pending.append(f"item {key}: design {dimension} remains unchecked")
            checked.append({"item": key, "dimension": dimension, "recorded_result": result})
        if stage == "delivery":
            for missing in DESIGN_DIMENSIONS:
                if missing not in seen:
                    pending.append(f"item {key}: design {missing} review missing")
    return {"enabled": True, "task": direction.get("task", "other"), "checks": checked,
            "required_dimensions": list(DESIGN_DIMENSIONS),
            "limits": "Checks explicit preservation declarations and version-bound review records, not actual geometry, aesthetic merit, or truth of reviewer claims. No fixed color-count, layout, lens, or lighting threshold is imposed."}


def check_project(project, base_dir, stage="plan", probe=False, ffprobe=None):
    project = obj(project, "project")
    if integer(project.get("schema_version"), "schema_version", 1) != 1:
        raise ManifestError("only schema_version 1 is supported")
    project_id = string(project.get("project_id"), "project_id")
    kind = project.get("kind")
    if kind not in {"image", "video"}:
        raise ManifestError("kind must be image or video")
    if stage not in {"plan", "delivery"}:
        raise ManifestError("stage must be plan or delivery")
    if probe and stage != "delivery":
        raise ManifestError("actual media probing is only available in delivery stage")
    integer(project.get("width"), "width", 1)
    integer(project.get("height"), "height", 1)
    text_required = boolean(project.get("text_required", False), "text_required")
    audio_required = boolean(project.get("audio_required", kind == "video"), "audio_required")
    characters = indexed(project.get("characters", []), "characters")
    assets = indexed(project.get("assets", []), "assets")
    items = indexed(project.get("items"), "items")
    if not items:
        raise ManifestError("at least one item is required")
    for key, character in characters.items():
        if not strings(character.get("anchors"), f"characters.{key}.anchors"):
            raise ManifestError(f"character {key} needs identity anchors")

    errors, warnings, pending = [], [], []
    measured_assets, timeline, reviews = {}, [], []
    capability_report = check_production_rules(project, items, assets, errors, warnings)
    for key, asset in assets.items():
        location = string(asset.get("path"), f"assets.{key}.path")
        if "://" in location or location.startswith(("\\\\", "//")):
            raise ManifestError("asset paths must be local; this helper never fetches URLs")
        boolean(asset.get("approved", False), f"assets.{key}.approved")
        expected_hash = asset.get("sha256")
        if expected_hash is not None:
            if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(
                c not in "0123456789abcdefABCDEF" for c in expected_hash
            ):
                raise ManifestError(f"assets.{key}.sha256 must be a 64-character hex digest")
        if stage == "delivery":
            path = (Path(base_dir) / location).resolve()
            if not path.is_file():
                errors.append(f"asset {key}: missing file {path}")
                continue
            try:
                actual_hash = sha256(path)
                size = path.stat().st_size
            except OSError as exc:
                errors.append(f"asset {key}: cannot read file ({type(exc).__name__})")
                continue
            measured_assets[key] = {"path": str(path), "sha256": actual_hash, "bytes": size}
            if size == 0:
                errors.append(f"asset {key}: empty file")
            if expected_hash is not None and expected_hash.lower() != actual_hash:
                errors.append(f"asset {key}: declared hash differs from actual file")

    direction_report = check_design_direction(project, items, assets, measured_assets, stage, errors, warnings, pending)
    fps = None
    if kind == "video":
        fps_value = project.get("fps")
        if isinstance(fps_value, bool) or not isinstance(fps_value, (str, int)):
            raise ManifestError("fps must be a positive integer or rational string")
        try:
            fps = Fraction(fps_value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ManifestError("invalid fps") from exc
        if fps <= 0:
            raise ManifestError("fps must be positive")
        target = integer(project.get("target_frames"), "target_frames", 1)

    expected_dimensions = {"brief", "identity", "structure", "composition", "export"}
    if text_required:
        expected_dimensions.add("text")
    if len(items) > 1:
        expected_dimensions.add("continuity")
    if kind == "video":
        expected_dimensions.add("motion")
        expected_dimensions.add("continuity")
        if audio_required:
            expected_dimensions.add("sound")

    cursor, previous_frames, previous_overlap = 0, None, 0
    for i, (key, item) in enumerate(items.items()):
        string(item.get("prompt"), f"items.{key}.prompt")
        for field, index in (("characters", characters), ("references", assets)):
            ids = strings(item.get(field, []), f"items.{key}.{field}")
            for ref in ids:
                if ref not in index:
                    errors.append(f"item {key}: unknown {field} id {ref}")
        strings(item.get("keep", []), f"items.{key}.keep")
        if kind == "video":
            frames = integer(item.get("frames"), f"items.{key}.frames", 1)
            overlap = integer(item.get("overlap_previous_frames", 0), f"items.{key}.overlap", 0)
            if i == 0 and overlap:
                errors.append(f"item {key}: first item cannot overlap a previous item")
            if overlap >= frames or (previous_frames is not None and overlap >= previous_frames):
                errors.append(f"item {key}: overlap must be shorter than both adjacent items")
            if previous_frames is not None and previous_overlap + overlap > previous_frames:
                errors.append(f"item {key}: adjacent transitions create an unplanned three-item overlap")
            start = cursor - overlap
            cursor = start + frames
            timeline.append({"id": key, "start_frame": start, "end_frame": cursor, "frames": frames})
            previous_frames, previous_overlap = frames, overlap

        output_id = item.get("output_asset_id")
        if output_id is not None:
            string(output_id, f"items.{key}.output_asset_id")
            if output_id not in assets:
                errors.append(f"item {key}: unknown output asset {output_id}")
        if stage == "delivery" and output_id is None:
            pending.append(f"item {key}: no output asset attached")
        if probe and output_id in measured_assets:
            from probe_media import ProbeError, probe_file, compare_output
            info = measured_assets[output_id]
            try:
                media = probe_file(info["path"], ffprobe)
                info["media"] = media
                media_errors, media_pending = compare_output(project, item, media)
                errors.extend(f"item {key}: {e}" for e in media_errors)
                pending.extend(f"item {key}: {e}" for e in media_pending)
            except ProbeError as exc:
                (pending if exc.unavailable else errors).append(f"item {key}: {exc}")
        item_reviews = sequence(item.get("reviews", []), f"items.{key}.reviews")
        seen_dimensions = set()
        for j, review in enumerate(item_reviews):
            review = obj(review, f"items.{key}.reviews[{j}]")
            dimension = string(review.get("dimension"), "review.dimension")
            if dimension not in expected_dimensions:
                raise ManifestError(f"item {key}: review dimension {dimension} is not applicable")
            if dimension in seen_dimensions:
                raise ManifestError(f"item {key}: duplicate review dimension {dimension}")
            seen_dimensions.add(dimension)
            result = review.get("result")
            if result not in {"pass", "fail", "unknown"}:
                raise ManifestError("review.result must be pass, fail or unknown")
            if result in {"pass", "fail"}:
                for field in ("evidence", "reviewer", "method", "asset_id", "sha256"):
                    string(review.get(field), f"review.{field}")
                methods = {"image_view", "video_playback", "audio_listen", "media_probe", "user_review"}
                if review["method"] not in methods:
                    raise ManifestError("unknown review method")
                if dimension == "motion" and review["method"] != "video_playback":
                    errors.append(f"item {key}: motion requires actual video playback")
                if dimension == "sound" and review["method"] != "audio_listen":
                    errors.append(f"item {key}: sound requires actual listening")
                if dimension == "export" and review["method"] != "media_probe":
                    errors.append(f"item {key}: export requires probing the actual file")
                if review["asset_id"] != output_id:
                    errors.append(f"item {key}: review does not refer to its output asset")
                if stage == "delivery":
                    asset_info = measured_assets.get(output_id)
                    if asset_info is None or review["sha256"].lower() != asset_info["sha256"]:
                        errors.append(f"item {key}: stale or unverifiable {dimension} review")
            if stage == "delivery":
                if result == "fail":
                    errors.append(f"item {key}: {dimension} review failed")
                elif result == "unknown":
                    pending.append(f"item {key}: {dimension} remains unchecked")
            reviews.append({"item": key, "dimension": dimension, "recorded_result": result})
        if stage == "delivery":
            for missing in sorted(expected_dimensions - seen_dimensions):
                pending.append(f"item {key}: {missing} review missing")

    subtitle_stats = []
    if kind == "video":
        if cursor != target:
            errors.append(f"timeline has {cursor} frames; target is {target}")
        subtitles = sequence(project.get("subtitles", []), "subtitles")
        if subtitles and not text_required:
            errors.append("subtitles exist but text_required is false")
        char_limit = project.get("subtitle_max_chars")
        if char_limit is not None:
            integer(char_limit, "subtitle_max_chars", 1)
        cps_limit = project.get("subtitle_max_cps")
        if cps_limit is not None:
            cps_limit = amount(cps_limit, "subtitle_max_cps")
            if cps_limit == 0:
                raise ManifestError("subtitle_max_cps must be positive")
        tracks = {}
        for i, subtitle in enumerate(subtitles):
            subtitle = obj(subtitle, f"subtitles[{i}]")
            start = integer(subtitle.get("start_frame"), "subtitle.start_frame")
            end = integer(subtitle.get("end_frame"), "subtitle.end_frame", 1)
            line = string(subtitle.get("text"), "subtitle.text")
            track = string(subtitle.get("track", "main"), "subtitle.track")
            if start >= end or end > cursor:
                errors.append(f"subtitle {i}: invalid range [{start}, {end}) for {cursor} frames")
            count = sum(not char.isspace() for char in line)
            cps = Fraction(count) * fps / (end - start) if end > start else None
            if char_limit is not None and count > char_limit:
                warnings.append(f"subtitle {i}: {count} non-whitespace code points exceed {char_limit}")
            if cps is not None and cps_limit is not None and cps > Fraction(cps_limit):
                warnings.append(f"subtitle {i}: reading-speed estimate exceeds configured limit")
            subtitle_stats.append({"index": i, "code_points": count, "estimated_cps": float(cps) if cps else None})
            tracks.setdefault(track, []).append((start, end, i))
        for track, intervals in tracks.items():
            active_end = -1
            for start, end, index in sorted(intervals):
                if start < active_end:
                    errors.append(f"subtitle {index}: overlapping subtitles on track {track}")
                active_end = max(active_end, end)

    budget = project.get("budget")
    budget_report = {"status": "unknown"}
    if budget is None:
        warnings.append("budget is unspecified; no generation/spending authorization is implied")
    else:
        budget = obj(budget, "budget")
        currency = string(budget.get("currency"), "budget.currency")
        cap = amount(budget.get("limit"), "budget.limit")
        spent = amount(budget.get("spent", 0), "budget.spent")
        calls = integer(budget.get("planned_new_calls"), "budget.planned_new_calls")
        call_cap = integer(budget.get("max_new_calls"), "budget.max_new_calls")
        estimate = budget.get("estimated_next_cost")
        over_limit = spent > cap or calls > call_cap
        if estimate is not None:
            estimate = amount(estimate, "budget.estimated_next_cost")
            over_limit = over_limit or spent + estimate > cap
        else:
            warnings.append("next cost is unknown; do not treat it as zero")
        if over_limit:
            errors.append("budget or planned generation-call limit exceeded")
        budget_report = {
            "status": "over_limit" if over_limit else ("within_limit" if estimate is not None else "unknown"),
            "currency": currency, "remaining": str(cap - spent),
            "estimated_next_cost": str(estimate) if estimate is not None else None,
            "planned_new_calls": calls,
        }

    groups = {}
    for key, info in measured_assets.items():
        groups.setdefault(info["sha256"], []).append(key)
    duplicate_files = [keys for keys in groups.values() if len(keys) > 1]
    if duplicate_files:
        warnings.append("some asset IDs refer to identical bytes; review reuse, not automatic regeneration")
    status = "needs_revision" if errors else (
        "pending_review" if stage == "delivery" and pending else (
            "recorded_delivery_ready" if stage == "delivery" else "plan_data_valid"
        )
    )
    return {
        "project_id": project_id, "stage": stage, "status": status,
        "errors": errors, "warnings": warnings, "pending": pending,
        "timeline": timeline, "total_frames": cursor if fps else None,
        "duration_seconds_exact": str(Fraction(cursor) / fps) if fps else None,
        "duration_seconds": float(Fraction(cursor) / fps) if fps else None,
        "subtitle_stats": subtitle_stats, "budget": budget_report,
        "capabilities": capability_report, "required_review_dimensions": sorted(expected_dimensions),
        "design_direction": direction_report,
        "actual_media_probe_requested": probe,
        "measured_assets": measured_assets, "duplicate_files": duplicate_files,
        "reviews": reviews,
        "limits": "Checks manifest data and file/version links; --probe additionally reads media metadata. It does not inspect visuals, play/listen, fully decode, or verify reviewer claims. Plan validity is not generation authorization; recorded delivery readiness requires real review outside this helper.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--stage", choices=("plan", "delivery"), default="plan")
    parser.add_argument("--probe", action="store_true", help="Read actual media metadata using an existing ffprobe")
    parser.add_argument("--ffprobe", help="Explicit path to an existing local ffprobe executable")
    args = parser.parse_args(argv)
    try:
        project = json.loads(args.manifest.read_text(encoding="utf-8-sig"), parse_float=Decimal)
        report = check_project(project, args.manifest.parent, args.stage, args.probe, args.ffprobe)
    except (ManifestError, OSError, ValueError, TypeError, OverflowError) as exc:
        print(json.dumps({"status": "invalid_manifest", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["errors"]:
        return 1
    return 3 if args.stage == "delivery" and report["pending"] else 0


if __name__ == "__main__":
    sys.exit(main())
