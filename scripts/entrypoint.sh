#!/bin/bash
# Entrypoint script para organizar workspace automaticamente

# Criar estrutura correta se não existir
mkdir -p /workspace/projects
mkdir -p /workspace/results
mkdir -p /workspace/scripts

# Mover jsoup se existir no lugar errado
if [ -d "/workspace/jsoup" ] && [ ! -d "/workspace/projects/jsoup" ]; then
    echo "Organizando workspace: movendo jsoup para projects/"
    mv /workspace/jsoup /workspace/projects/
fi

# Remover diretórios antigos em português (vazios)
[ -d "/workspace/projetos" ] && [ -z "$(ls -A /workspace/projetos 2>/dev/null)" ] && rm -rf /workspace/projetos
[ -d "/workspace/resultados" ] && [ -z "$(ls -A /workspace/resultados 2>/dev/null)" ] && rm -rf /workspace/resultados

# Executar comando passado como argumento
exec "$@"
