#!/bin/bash
# Entrypoint script para inicializar workspace

# Criar estrutura de diretórios padrão se não existir
mkdir -p /workspace/projects
mkdir -p /workspace/results
mkdir -p /workspace/scripts

# Executar comando passado como argumento
exec "$@"
