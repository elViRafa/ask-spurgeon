## To Ollama
$env:MEMORY_FABRIC_LLM_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "gemma4"


## To Open web ui
# 1. Defina o provedor como openai (pois o Open WebUI usa formato compatível)
#$env:MEMORY_FABRIC_LLM_PROVIDER = "openai"

# 2. Defina a URL base da API do seu Open WebUI (normalmente o caminho /api)
#$env:OPENAI_BASE_URL = "http://localhost:3000/api"

# 3. Defina o nome do modelo que você deseja usar no Open WebUI
#$env:OPENAI_MODEL = "gemma4:latest"  # ex: gemma2, gemma4 ou spurgeon-8b

# 4. (Opcional) Chave de API se o seu Open WebUI exigir (caso contrário, o sistema usará "dummy" automaticamente)
#$env:OPENAI_API_KEY = "sk-655543d9b70a4ddbb6274043c6dc0c02"
