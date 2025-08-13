#!/bin/bash

# Setup script for Ollama with popular models

echo "Setting up Ollama with popular models..."

# Start Ollama service
echo "Starting Ollama..."
docker-compose up -d ollama

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
sleep 30

# Function to pull model with retry
pull_model() {
    local model=$1
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Pulling $model (attempt $attempt/$max_attempts)..."
        if docker exec lang_graph_ollama ollama pull $model; then
            echo "Successfully pulled $model"
            return 0
        else
            echo "Failed to pull $model (attempt $attempt)"
            attempt=$((attempt + 1))
            sleep 10
        fi
    done
    
    echo "Failed to pull $model after $max_attempts attempts"
    return 1
}

# Pull popular models
echo "Pulling popular models..."

# Small, fast models
pull_model "llama3.2:1b"
pull_model "llama3.2:3b"

# Medium models
pull_model "llama3.1:8b"
pull_model "mistral:7b"
pull_model "codellama:7b"

# Large models (optional, comment out if resources are limited)
# pull_model "llama3.1:70b"
# pull_model "codellama:34b"

# Specialized models
pull_model "nomic-embed-text"  # For embeddings
pull_model "all-minilm"        # For embeddings

echo "Listing available models..."
docker exec lang_graph_ollama ollama list

echo "Ollama setup complete!"
echo "You can access Ollama at http://localhost:11434"
echo "Web UI is available at http://localhost:3000"

# Test a simple completion
echo "Testing with a simple completion..."
docker exec lang_graph_ollama ollama run llama3.2:1b "Hello, how are you?" || echo "Test failed, but setup is complete"