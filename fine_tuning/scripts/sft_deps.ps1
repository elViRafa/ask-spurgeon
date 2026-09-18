# Pinned / minimum versions for SFT GATE-0 on RunPod (torch 2.11+ for transformers 5.x / torchao).
$SFT_TORCH_MIN = "2.11.0"
$SFT_TORCH_INDEX = "https://download.pytorch.org/whl/cu126"
$SFT_PIP_EXTRAS = @(
    "datasets>=3.0.0",
    "peft>=0.14.0",
    "trl>=0.18.0",
    "transformers>=4.51.0",
    "huggingface_hub>=0.26.0"
)
