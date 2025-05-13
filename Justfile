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
    uv export --only-group agents -o app/agents/requirements.txt

    # MCP
    uv export --only-group mcp-rag -o app/mcp/rag/requirements.txt

    # RAG
    uv export --only-group rag-ui -o app/rag/rag-ui/requirements.txt


# LLM
stop-llm:
    docker-compose --profile llm -p llm-lab -f docker/docker-compose.yml down

start-llm: stop-llm
    docker-compose --profile llm -p llm-lab -f docker/docker-compose.yml up -d

# Agent
stop-agent:
    docker-compose --profile agent -p agent-lab -f docker/docker-compose.yml down

start-agent: stop-agent
    docker-compose --profile agent -p agent-lab -f docker/docker-compose.yml up -d

# RAG
stop-rag:
    docker-compose --profile rag -p rag-lab -f docker/docker-compose.yml down

start-rag: stop-rag
    docker-compose --profile rag -p rag-lab -f docker/docker-compose.yml up -d

# MCP
stop-mcp:
    docker-compose -p mcp-lab -f docker/docker-compose-mcp.yml down

start-mcp: stop-mcp
    docker-compose -p mcp-lab -f docker/docker-compose-mcp.yml up -d
