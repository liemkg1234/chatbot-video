#!/bin/bash

echo "Starting Ollama server..."
ollama serve &
sleep 5

ollama run hf.co/mradermacher/SmolVLM2-2.2B-Instruct-i1-GGUF:Q4_K_M

ollama list

tail -f /dev/null