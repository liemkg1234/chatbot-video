FROM node:20-slim AS builder

RUN npm install -g @kevinwatt/yt-dlp-mcp

RUN mkdir -p /mcp && \
    cp -r /usr/local/lib/node_modules /mcp/node_modules && \
    cp -r /usr/local/bin /mcp/bin

FROM python:3.12-slim AS runtime

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install --no-cache-dir yt-dlp && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /mcp/node_modules /usr/local/lib/node_modules
COPY --from=builder /mcp/bin /usr/local/bin

WORKDIR /app

CMD ["yt-dlp-mcp"]