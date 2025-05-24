FROM foundationmodels/flash-attention:fastapi

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install -q --upgrade transformers==4.51.0 accelerate flash-attn num2words av

COPY . .

EXPOSE 8000

ENV PATH="/usr/local/bin:$PATH" \
    UV_PYTHON_PREFERENCE=only-system

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]