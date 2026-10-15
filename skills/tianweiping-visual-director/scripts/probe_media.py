#!/usr/bin/env python3
"""Probe local media metadata; never generate, modify, or visually evaluate media."""

import argparse
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


class ProbeError(ValueError):
    def __init__(self, message, unavailable=False):
        super().__init__(message)
        self.unavailable = unavailable


def rational(value):
    try:
        result = Fraction(str(value))
        return result if result > 0 else None
    except (ValueError, ZeroDivisionError):
        return None


def probe_file(path, executable=None, timeout=15):
    if "://" in str(path) or str(path).startswith(("\\\\", "//")):
        raise ProbeError("only local media paths are supported")
    path = Path(path).resolve()
    if not path.is_file():
        raise ProbeError("media file is missing")
    executable = executable or shutil.which("ffprobe")
    if not executable or not Path(executable).is_file():
        raise ProbeError("ffprobe unavailable; provide --ffprobe with an existing executable", unavailable=True)
    command = [str(Path(executable).resolve()), "-v", "error", "-protocol_whitelist", "file",
               "-show_format", "-show_streams",
               "-of", "json", str(path)]
    try:
        result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ProbeError("media probe timed out; result remains unknown", unavailable=True) from exc
    except OSError as exc:
        raise ProbeError("ffprobe could not run", unavailable=True) from exc
    if result.returncode:
        raise ProbeError("ffprobe could not read the media: " + result.stderr.strip()[:400])
    try:
        raw = json.loads(result.stdout)
        streams = raw.get("streams", [])
        if not isinstance(streams, list) or not streams:
            raise ValueError("no streams")
    except (ValueError, AttributeError) as exc:
        raise ProbeError("ffprobe did not return valid media-stream metadata") from exc
    selected = []
    keys = {"index", "codec_type", "codec_name", "width", "height", "avg_frame_rate", "r_frame_rate",
            "nb_frames", "duration", "sample_rate", "channels"}
    for stream in streams:
        record = {key: stream[key] for key in keys if key in stream}
        record["disposition"] = {"attached_pic": stream.get("disposition", {}).get("attached_pic", 0)}
        record["side_data_list"] = [{"rotation": side["rotation"]} for side in stream.get("side_data_list", []) if "rotation" in side]
        rotation_tag = stream.get("tags", {}).get("rotate")
        if rotation_tag is not None:
            try:
                record["side_data_list"].append({"rotation": float(rotation_tag)})
            except ValueError:
                record["side_data_list"].append({"rotation": "unknown"})
        selected.append(record)
    return {"tool": str(Path(executable).resolve()), "streams": selected,
            "format": {key: value for key, value in raw.get("format", {}).items() if key in {"format_name", "duration"}},
            "scope": "Container/stream metadata only; frame counts may be header values. No full decode or visual/audio review."}


def compare_output(project, item, media):
    errors, pending = [], []
    videos = [s for s in media["streams"] if s.get("codec_type") == "video" and
              not s.get("disposition", {}).get("attached_pic", 0)]
    if len(videos) != 1:
        return ["expected one primary visual stream"], []
    video = videos[0]
    if video.get("width") != project["width"] or video.get("height") != project["height"]:
        errors.append("actual pixel dimensions differ from project dimensions")
    rotations = [s.get("rotation", 0) for s in video.get("side_data_list", [])]
    if any(rotation not in (0, 360, -360) for rotation in rotations):
        pending.append("rotation metadata needs display-orientation verification")
    if project["kind"] == "image":
        image_codecs = {"png", "mjpeg", "webp", "bmp", "tiff", "gif", "jpeg2000", "svg", "av1"}
        if video.get("codec_name") not in image_codecs:
            errors.append("image output does not use a recognized still-image codec")
        frames = video.get("nb_frames")
        if frames is not None and str(frames).isdigit() and int(frames) > 1:
            errors.append("image output has multiple frames; verify animated-image intent separately")
        return errors, pending
    rate = rational(video.get("avg_frame_rate"))
    if rate is None:
        pending.append("actual average frame rate is unavailable")
    elif rate != Fraction(str(project["fps"])):
        errors.append("actual average frame rate differs from project fps")
    audio = [s for s in media["streams"] if s.get("codec_type") == "audio"]
    if project.get("audio_required", True) and not audio:
        errors.append("expected audio stream is missing")
    if not project.get("audio_required", True) and audio:
        errors.append("silent-output project contains an audio stream")
    available = video.get("nb_frames")
    count_from_header = available is not None and str(available).isdigit()
    if count_from_header:
        available = Fraction(int(available))
    else:
        duration = rational(video.get("duration")) or rational(media.get("format", {}).get("duration"))
        available = duration * rate if duration and rate else None
    required = item["frames"] + item.get("trim_in_frame", 0)
    if available is None:
        pending.append("available frame coverage is unknown")
    elif available < required and (count_from_header or available + 1 < required):
        errors.append("source media is too short for the selected edit range")
    elif available < required:
        pending.append("estimated duration is near edit boundary; actual frame count needs verification")
    if item.get("exact_output_frames", False):
        if item.get("trim_in_frame", 0):
            errors.append("exact output-frame check cannot also trim the source")
        if available is not None and (available != item["frames"] if count_from_header else abs(available - item["frames"]) > 1):
            errors.append("actual output duration differs from exact edited duration")
        elif available is not None and not count_from_header:
            pending.append("exact output frame count is not available in metadata")
    return errors, pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path)
    parser.add_argument("--ffprobe")
    args = parser.parse_args()
    try:
        report = probe_file(args.media, args.ffprobe)
    except ProbeError as exc:
        print(json.dumps({"status": "unknown" if exc.unavailable else "failed", "error": str(exc)}, ensure_ascii=False))
        return 3 if exc.unavailable else 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
