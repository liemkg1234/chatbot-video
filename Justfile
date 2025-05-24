# Setup local
clear-venv:
    rm -rf .venv .uv_cache

install:
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv sync --all-groups --cache-dir .uv_cache

install-hooks:
    uv run pre-commit install

setup: clear-venv install
    echo "Setup done. Run 'source .venv/bin/activate' to activate the virtual environment."


# Format code
lint:
    ruff check .

fmt:
    uv run ruff check --fix
    uv run isort ./app


# Server
dependency:
    # Agents
    uv export --only-group vlm -o app/vlm/requirements.txt

# Download model
download-model:
    sudo mkdir docker/volumes/models
    wget -O https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf docker/volumes/models/Qwen3-8B-Q4_K_M.gguf

    wget -O https://huggingface.co/ggml-org/InternVL3-8B-Instruct-GGUF/resolve/main/InternVL3-8B-Instruct-Q4_K_M.gguf docker/volumes/models/InternVL3-8B-Instruct-Q4_K_M.gguf

# LLM
stop:
    docker-compose -p chat-video -f docker/docker-compose-ai.yml down

start: stop
    docker-compose -p chat-video -f docker/docker-compose-ai.yml up -d
