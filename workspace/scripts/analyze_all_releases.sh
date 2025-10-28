#!/bin/bash

# Script para analisar todas as releases de um projeto Java
# Uso: ./analyze_all_releases.sh <nome-do-projeto>

set -e

if [ -z "$1" ]; then
    echo "Uso: $0 <nome-do-projeto>"
    echo "Exemplo: $0 meu-projeto"
    exit 1
fi

PROJECT_NAME=$1
PROJECT_DIR="/workspace/projetos/$PROJECT_NAME"
RESULTS_DIR="/workspace/resultados/$PROJECT_NAME"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Erro: Projeto não encontrado em $PROJECT_DIR"
    exit 1
fi

echo "==================================="
echo "Análise de Qualidade de Software"
echo "Projeto: $PROJECT_NAME"
echo "==================================="

cd $PROJECT_DIR

# Verificar se é um repositório git
if [ ! -d ".git" ]; then
    echo "Erro: $PROJECT_DIR não é um repositório git"
    exit 1
fi

# Listar todas as tags
tags=$(git tag -l | sort -V)
tag_count=$(echo "$tags" | wc -l)

echo "Total de releases encontradas: $tag_count"
echo ""

# Criar diretório de resultados
mkdir -p "$RESULTS_DIR"

# Arquivo CSV para consolidar métricas
echo "release,date,commits,wmc,dit,noc,cbo,lcom,rfc,loc,bugs_total,bugs_security" > "$RESULTS_DIR/metrics_summary.csv"

counter=0

for tag in $tags; do
    counter=$((counter + 1))
    echo "[$counter/$tag_count] Analisando release: $tag"

    # Checkout da tag
    git checkout $tag 2>/dev/null

    # Data do commit da tag
    tag_date=$(git log -1 --format=%ai)

    # Criar diretório para resultados desta release
    release_dir="$RESULTS_DIR/$tag"
    mkdir -p "$release_dir"

    echo "  - Compilando projeto..."
    # Tentar compilar com Maven ou Gradle
    if [ -f "pom.xml" ]; then
        mvn clean package -DskipTests -q > "$release_dir/build.log" 2>&1 || echo "    Falha na compilação (verificar build.log)"
    elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
        gradle clean build -x test --quiet > "$release_dir/build.log" 2>&1 || echo "    Falha na compilação (verificar build.log)"
    else
        echo "    Sistema de build não detectado"
        continue
    fi

    echo "  - Extraindo métricas CK..."
    ck "$PROJECT_DIR" "$release_dir/ck" > /dev/null 2>&1 || echo "    Erro ao executar CK"

    echo "  - Executando SpotBugs..."
    # Procurar JARs compilados
    jar_files=$(find target -name "*.jar" -not -name "*sources*" -not -name "*javadoc*" 2>/dev/null || find build/libs -name "*.jar" 2>/dev/null || echo "")

    if [ -n "$jar_files" ]; then
        for jar in $jar_files; do
            spotbugs -textui \
                -effort:max \
                -pluginList /tools/spotbugs/plugin/findsecbugs-plugin.jar \
                -xml:withMessages \
                -output "$release_dir/spotbugs.xml" \
                "$jar" > /dev/null 2>&1 || echo "    Erro ao executar SpotBugs"
        done
    else
        echo "    Nenhum JAR encontrado para análise"
    fi

    echo "  - Análise concluída para $tag"
    echo ""
done

# Voltar para branch principal
git checkout main 2>/dev/null || git checkout master 2>/dev/null || true

echo "==================================="
echo "Análise Concluída!"
echo "Resultados salvos em: $RESULTS_DIR"
echo "==================================="
echo ""
echo "Próximos passos:"
echo "1. Executar RefactoringMiner no repositório completo"
echo "2. Consolidar dados com script Python"
echo "3. Gerar gráficos e estatísticas"
