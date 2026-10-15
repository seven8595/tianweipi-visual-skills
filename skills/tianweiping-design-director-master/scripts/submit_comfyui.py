"""
submit_comfyui.py — 把商业街效果图 prompt 直接提交到本机 ComfyUI。

本机已配置（2026-10-07）：
- ComfyUI 路径: F:\\AI\\ComfyUI
- venv Python:  F:\\AI\\ComfyUI\\venv\\Scripts\\python.exe
- 本地 API:     http://127.0.0.1:8188
- Tailscale:    http://100.77.54.21:8188（手机/Mac 用）

用法示例：
    python submit_comfyui.py \\
        --positive "architectural visualization, premium modern open-air shopping district, blue hour, ..." \\
        --negative "low quality, cartoon, ..." \\
        --checkpoint "flux1-dev-fp8.safetensors" \\
        --width 1344 --height 768 --steps 24 --cfg 3.5 --seed 42

参数：
    --positive     正向 prompt（必填）
    --negative     负向 prompt（必填）
    --checkpoint   ComfyUI/models/checkpoints 下的文件名（必填）
    --width        默认 1344
    --height       默认 768
    --steps        默认 24
    --cfg          Flux 用 guidance，默认 3.5；SDXL 一般 6-7
    --seed         默认 -1（随机）
    --host         默认 100.77.54.21:8188（Tailscale，手机/Mac/本地都能连）

输出：
    打印 prompt_id，然后图片会保存到 ComfyUI/output/ 目录。
"""
import argparse
import json
import time
import urllib.request
import urllib.error
import uuid
import sys


# 本机配置（硬编码，避免每次探测）
COMFYUI_HOST = "100.77.54.21:8188"   # Tailscale IP
COMFYUI_LOCAL = "127.0.0.1:8188"     # 本地回退
COMFYUI_OUTPUT_DIR = r"F:\AI\ComfyUI\output"


def build_workflow(args):
    """构造一个最简 ComfyUI 文生图 workflow (API 格式)。"""
    client_id = str(uuid.uuid4())
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": args.seed,
                "steps": args.steps,
                "cfg": args.cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": args.checkpoint}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": args.width, "height": args.height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": args.positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": args.negative, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "commercial_street", "images": ["8", 0]}},
    }, client_id


def check_comfyui_running(host):
    """快速探测 ComfyUI 是否在跑。"""
    try:
        with urllib.request.urlopen(f"http://{host}/system_stats", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--positive", required=True)
    p.add_argument("--negative", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--width", type=int, default=1344)
    p.add_argument("--height", type=int, default=768)
    p.add_argument("--steps", type=int, default=24)
    p.add_argument("--cfg", type=float, default=3.5)
    p.add_argument("--seed", type=int, default=-1)
    p.add_argument("--host", default=COMFYUI_HOST,
                   help=f"默认 Tailscale IP {COMFYUI_HOST}；本地调试用 {COMFYUI_LOCAL}")
    args = p.parse_args()

    # 先探测 ComfyUI 是否在跑，不通则回退到本地 127.0.0.1
    if not check_comfyui_running(args.host):
        print(f"[WARN] {args.host} 不通，尝试本地 {COMFYUI_LOCAL} ...")
        if check_comfyui_running(COMFYUI_LOCAL):
            args.host = COMFYUI_LOCAL
        else:
            print(f"[FAIL] ComfyUI 没在跑。请先启动：")
            print(f'  Start-Process -FilePath "F:\\AI\\ComfyUI\\venv\\Scripts\\python.exe" '
                  f'-ArgumentList "main.py --listen 0.0.0.0 --port 8188 --highvram" '
                  f'-WorkingDirectory "F:\\AI\\ComfyUI" -WindowStyle Hidden')
            sys.exit(1)

    workflow, client_id = build_workflow(args)
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode("utf-8")
    req = urllib.request.Request(
        f"http://{args.host}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] ComfyUI accepted via {args.host}")
            print(f"     prompt_id = {data.get('prompt_id')}")
            print(f"     图片会保存到 {COMFYUI_OUTPUT_DIR}")
    except urllib.error.URLError as e:
        print(f"[FAIL] 无法连接 ComfyUI http://{args.host} : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
