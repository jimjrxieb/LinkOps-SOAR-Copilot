#!/usr/bin/env bash
set -euo pipefail

echo "=== GPU & CUDA Sanity for WSL (no venv) ==="

echo "[1/7] Windows/WSL driver check"
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: nvidia-smi not found in WSL. Install/update NVIDIA driver w/ WSL support on Windows, then `sudo apt install -y nvidia-cuda-toolkit` in WSL."
  exit 1
fi
nvidia-smi | head -n 10

echo "[2/7] Python baseline"
PY=$(command -v python3 || true)
[ -z "$PY" ] && { echo "ERROR: python3 not found"; exit 1; }
echo "python: $PY"
$PY -V

echo "[3/7] Ensure CUDA-enabled PyTorch (not CPU-only)"
pip3 uninstall -y torch torchvision torchaudio 2>/dev/null || true
pip3 install --index-url https://download.pytorch.org/whl/cu121 torch torchvision --upgrade

echo "[4/7] bitsandbytes for 4-bit (NVIDIA only)"
pip3 install -U bitsandbytes accelerate transformers

echo "[5/7] Quick CUDA probe"
python3 - <<'PY'
import torch, platform
print("cuda_available:", torch.cuda.is_available())
if torch.cuda.is_available():
  print("device:", torch.cuda.get_device_name(0))
  print("capability:", torch.cuda.get_device_capability(0))
print("torch:", torch.__version__, "python:", platform.python_version())
try:
  import bitsandbytes as bnb; print("bitsandbytes:", bnb.__version__)
except Exception as e: print("bitsandbytes import error:", e)
PY

echo "[6/7] Minimal on-GPU load + 1 short generation (uses cache if present)"
export TRANSFORMERS_OFFLINE=0
export HF_HUB_ENABLE_HF_TRANSFER=1
python3 - <<'PY'
import os, torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
mid = "Qwen/Qwen2.5-3B-Instruct"   # smaller/faster sanity model; swap to CodeLlama later
tok = AutoTokenizer.from_pretrained(mid, use_fast=True)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
m = AutoModelForCausalLM.from_pretrained(mid, quantization_config=bnb, device_map="auto", trust_remote_code=False)
ids = tok("Say: GPU sanity OK.", return_tensors="pt").to(m.device)
with torch.inference_mode():
    out = m.generate(**ids, max_new_tokens=8)
print(tok.decode(out[0], skip_special_tokens=True))
if torch.cuda.is_available():
    print("VRAM GB allocated:", round(torch.cuda.memory_allocated()/1e9,2))
PY

echo "[7/7] Live GPU view (10 seconds)"
for i in {1..5}; do nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits; sleep 2; done

echo "=== Done. If gpu util stays 0 and VRAM ~0 -> CUDA wheel or driver mismatch. ==="