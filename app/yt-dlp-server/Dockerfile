FROM jauderho/yt-dlp:latest

RUN apk add --no-cache python3

WORKDIR /app
COPY . .

RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir -p /temp

EXPOSE 8000

ENTRYPOINT ["dumb-init"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]