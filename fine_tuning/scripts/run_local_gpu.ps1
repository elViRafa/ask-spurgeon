# PowerShell Script to run the Spurgeon fine-tuned model locally using NVIDIA GPU (CUDA 12.4)
# Target GPU: NVIDIA GeForce RTX 2070 Super (8GB VRAM)

$ProjectRoot = Resolve-Path "$PSScriptRoot\..\.."
$VenvPath = Join-Path $ProjectRoot ".venv"
$ModelPath = Join-Path $ProjectRoot "fine_tuning\models\Spurgeon-8B-Q4_K_M.gguf"
$ServerScript = Join-Path $ProjectRoot "fine_tuning\spaces\cpu-llama-cpp\main.py"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Starting Spurgeon Local GPU Server (CUDA 12.4)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check virtual environment
if (Test-Path $VenvPath) {
    Write-Host "Activating virtual environment: $VenvPath" -ForegroundColor Green
    & "$VenvPath\Scripts\Activate.ps1"
} else {
    Write-Warning "Virtual environment (.venv) not found at $VenvPath. Using active/global Python environment."
}

# 2. Check model file
if (-not (Test-Path $ModelPath)) {
    Write-Error "Could not find local GGUF model at: $ModelPath"
    Write-Host "Please download or place Spurgeon-8B-Q4_K_M.gguf there first." -ForegroundColor Yellow
    Exit 1
} else {
    Write-Host "Found model file: $ModelPath" -ForegroundColor Green
}

# 3. Ask/Ensure llama-cpp-python with CUDA is installed
Write-Host "Ensuring llama-cpp-python is installed with CUDA 12.4 support..." -ForegroundColor Yellow
# Run pip install with the CUDA 12.4 prebuilt wheels index
python -m pip install --upgrade pip
python -m pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# 4. Set Environment Variables
Write-Host "Configuring GPU and local model variables..." -ForegroundColor Green
$env:LOCAL_MODEL_PATH = $ModelPath
$env:N_GPU_LAYERS = "-1"   # Offload all layers to GPU for RTX 2070 Super (8GB VRAM can fit 8B Q4_K_M completely!)
$env:N_CTX = "4096"
$env:N_THREADS = "4"       # CPU threads to coordinate with GPU

Write-Host "Running local server..." -ForegroundColor Cyan
Write-Host "Local endpoint will be available at: http://localhost:7860/v1" -ForegroundColor Green
Write-Host "To use this in your main Streamlit app, make sure to set the environment variable:" -ForegroundColor Yellow
Write-Host "  CUSTOM_LLM_BASE_URL = http://localhost:7860/v1" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Red
Write-Host "----------------------------------------------------------"

python $ServerScript
