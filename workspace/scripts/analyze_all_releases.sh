#!/bin/bash
# ==============================================================================
# Analisa releases reais (GitHub Releases) OU tags locais
# Usos típicos:
#   # usar releases oficiais (recomendado)
#   USE_RELEASES_CSV=1 ./analyze_all_releases.sh jsoup
#
#   # filtrar tags locais
#   TAG_FILTER='jsoup-1.*' ./analyze_all_releases.sh jsoup
#
#   # todas as tags locais
#   ./analyze_all_releases.sh jsoup
# ==============================================================================

set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Uso: $0 <nome-do-projeto>"
  exit 1
fi

PROJECT_NAME="$1"
PROJECT_DIR="/workspace/projetos/$PROJECT_NAME"
RESULTS_DIR="/workspace/resultados/$PROJECT_NAME"
CSV_PATH="$RESULTS_DIR/releases.csv"
JSON_PATH="$RESULTS_DIR/releases.json"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "Erro: $PROJECT_DIR não é um repositório git."
  exit 1
fi

mkdir -p "$RESULTS_DIR"
cd "$PROJECT_DIR"
git fetch --all --tags --prune >/dev/null 2>&1 || true

# ---------------------- Funções auxiliares ------------------------------------
has_tag()    { git rev-parse -q --verify "refs/tags/$1" >/dev/null 2>&1; }
has_commit() { git cat-file -e "$1^{commit}" >/dev/null 2>&1; }

checkout_ref() {
  local ref="$1"
  if has_tag "$ref";   then git checkout -f --detach "tags/$ref" >/dev/null 2>&1 && return 0; fi
  if has_commit "$ref"; then git checkout -f --detach "$ref"       >/dev/null 2>&1 && return 0; fi
  return 1
}

compile_project() {
  if   [ -f "pom.xml" ]; then
    # força um target razoável para releases antigas
    mvn -q -DskipTests -Dmaven.compiler.source=1.8 -Dmaven.compiler.target=1.8 clean package
  elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
    gradle -q clean build -x test
  else
    return 2
  fi
}

run_ck() { local outdir="$1"; ck "$PROJECT_DIR" "$outdir" >/dev/null 2>&1; }

run_spotbugs() {
  local outxml="$1"
  local jars
  jars=$( (find target -type f -name "*.jar" -not -name "*sources*" -not -name "*javadoc*" 2>/dev/null; \
           find build/libs -type f -name "*.jar" 2>/dev/null) | tr '\n' ' ')
  [ -z "$jars" ] && return 2
  spotbugs -textui -effort:max \
    -pluginList /tools/spotbugs/plugin/findsecbugs-plugin.jar \
    -xml:withMessages -output "$outxml" $jars >/dev/null 2>&1
}
# -----------------------------------------------------------------------------

echo "==================================="
echo "Análise de Qualidade de Software"
echo "Projeto: $PROJECT_NAME"
echo "==================================="

# --- Monta a lista de refs (tags ou hashes) com Python para evitar CSV quebrado
declare -a refs
if [ "${USE_RELEASES_CSV:-0}" = "1" ] && { [ -f "$JSON_PATH" ] || [ -f "$CSV_PATH" ]; }; then
  # exporta para o subprocesso Python enxergar
  export JSON_PATH CSV_PATH
  mapfile -t refs < <(python3 - <<'PY'
import os, json, pandas as pd

results = []
json_path = os.environ.get("JSON_PATH")
csv_path  = os.environ.get("CSV_PATH")

def clean(s):
    return (s or "").strip()

if json_path and os.path.isfile(json_path):
    data = json.load(open(json_path, "r", encoding="utf-8"))
    for r in data:
        # o extractor grava 'tag' e 'hash'
        tag = clean(r.get("tag"))
        h   = clean(r.get("hash"))
        results.append(tag if tag else h)
elif csv_path and os.path.isfile(csv_path):
    df = pd.read_csv(csv_path)  # pandas lida com multilinhas
    for _, row in df.iterrows():
        tag = clean(row.get("tag"))
        h   = clean(row.get("hash"))
        results.append(tag if tag else h)

# remove vazios e duplica preservando ordem
seen=set(); out=[]
for r in results:
    if r and r not in seen:
        out.append(r); seen.add(r)

print("\n".join(out))
PY
)
  echo "Total de releases encontradas (GitHub Releases): ${#refs[@]}"
  echo ""
else
  if [ -n "${TAG_FILTER:-}" ]; then
    mapfile -t refs < <(git tag -l | grep -E "$TAG_FILTER" | sort -V)
  else
    mapfile -t refs < <(git tag -l | sort -V)
  fi
  echo "Total de tags encontradas: ${#refs[@]}"
  echo ""
fi

summary_csv="$RESULTS_DIR/metrics_summary.csv"
echo "release,date,ck_class_rows,ck_method_rows,spotbugs_xml" > "$summary_csv"

count=0
for ref in "${refs[@]}"; do
  count=$((count+1))
  echo "[$count/${#refs[@]}] Analisando release/tag: $ref"

  if ! checkout_ref "$ref"; then
    echo "  - Referência não encontrada localmente, pulando"
    echo ""
    continue
  fi

  tag_date=$(git log -1 --format=%ai || echo "")
  release_dir="$RESULTS_DIR/$ref"
  mkdir -p "$release_dir"

  echo "  - Compilando projeto..."
  if ! compile_project >"$release_dir/build.log" 2>&1; then
    status=$?
    if [ $status -eq 2 ]; then
      echo "    Sistema de build não detectado"
    else
      echo "    Falha na compilação (verificar build.log)"
    fi
  fi

  echo "  - Extraindo métricas CK..."
  if run_ck "$release_dir/ck"; then
    ck_class_rows=$( [ -f "$release_dir/ck/class.csv" ]  && (wc -l < "$release_dir/ck/class.csv")  || echo 0 )
    ck_method_rows=$( [ -f "$release_dir/ck/method.csv" ] && (wc -l < "$release_dir/ck/method.csv") || echo 0 )
  else
    echo "    Erro ao executar CK"
    ck_class_rows=0
    ck_method_rows=0
  fi

  echo "  - Executando SpotBugs..."
  if run_spotbugs "$release_dir/spotbugs.xml"; then
    sb_path="$release_dir/spotbugs.xml"
  else
    echo "    Erro ao executar SpotBugs ou nenhum artefato encontrado"
    sb_path=""
  fi

  echo "$ref,$tag_date,$ck_class_rows,$ck_method_rows,$sb_path" >> "$summary_csv"
  echo "  - Análise concluída para $ref"
  echo ""
done

git checkout -f main 2>/dev/null || git checkout -f master 2>/dev/null || true

echo "==================================="
echo "Análise Concluída!"
echo "Resultados salvos em: $RESULTS_DIR"
echo "==================================="
echo ""
echo "Dicas:"
echo "- Para usar as *releases* do GitHub, gere antes $JSON_PATH/$CSV_PATH com: python3 /workspace/scripts/extract_releases.py jsoup --source=github"
echo "- Para filtrar tags: TAG_FILTER='jsoup-1.*' $0 $PROJECT_NAME"
