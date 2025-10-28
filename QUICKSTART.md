# 🚀 Guia Rápido - Ambiente Docker 75QUA

## Setup Inicial (5 minutos)

```bash
# 1. Construir e iniciar (primeira vez - ~10min)
make build && make up

# 2. Testar instalação
make test-tools
```

## Análise Automatizada (Recomendado)

### Um Único Comando

**Analisar todas as releases:**
```bash
make analyze REPO=jhy/jsoup
```

**Analisar primeiras 5 releases (teste rápido):**
```bash
make analyze-limit REPO=jhy/jsoup LIMIT=5
```

**Listar releases disponíveis:**
```bash
make list-releases REPO=jhy/jsoup
```

### O Que Acontece Automaticamente

1. ✅ Busca releases via GitHub API (apenas releases oficiais, não tags)
2. ✅ Clona/atualiza repositório em `workspace/projects/`
3. ✅ Para cada release:
   - Checkout da tag
   - Compilação (Maven/Gradle)
   - Extração de métricas CK (4 arquivos CSV)
   - Análise PMD (com logs)
   - SpotBugs + find-sec-bugs (com logs)
4. ✅ RefactoringMiner no repositório completo
5. ✅ Relatório resumido final

### Resultados

Tudo salvo em `workspace/results/<projeto>/`:

```
workspace/results/jsoup/
├── analysis-summary.txt          # Resumo geral
├── jsoup-1.12.2/
│   ├── ck/
│   │   ├── class.csv             # Métricas por classe
│   │   ├── method.csv            # Métricas por método
│   │   ├── field.csv             # Métricas por campo
│   │   └── variable.csv          # Métricas por variável
│   ├── pmd-report.csv            # Relatório PMD
│   ├── pmd.log                   # Logs PMD
│   ├── spotbugs-report.xml       # Relatório SpotBugs
│   ├── spotbugs.log              # Logs SpotBugs
│   ├── metadata.json             # Info da release
│   └── summary.json              # Resumo
├── jsoup-1.13.1/
│   └── ...
└── refactorings-all.json         # Todas as refatorações
```

Ver resultados:
```bash
cat workspace/results/jsoup/analysis-summary.txt
ls -la workspace/results/jsoup/
```

## Projetos Sugeridos

Projetos Java populares com ≥20 releases:

1. **jsoup** (20 releases) - `jhy/jsoup` - HTML parser
2. **Gson** (40+ releases) - `google/gson` - JSON library
3. **OkHttp** (100+ releases) - `square/okhttp` - HTTP client
4. **Apache Commons Lang** (100+ releases) - `apache/commons-lang`
5. **JUnit 5** (100+ releases) - `junit-team/junit5`

## Análise de Dados (Python/Jupyter)

```bash
# Iniciar Jupyter Notebook
make jupyter

# Acesse http://localhost:8888
```

Exemplo de análise:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Carregar métricas CK
df = pd.read_csv('workspace/results/jsoup/jsoup-1.12.2/ck/class.csv')

# Estatísticas
print(f"Classes: {len(df)}")
print(f"CBO médio: {df['cbo'].mean():.2f}")
print(f"WMC médio: {df['wmc'].mean():.2f}")

# Gráfico
df['wmc'].hist(bins=30)
plt.xlabel('WMC')
plt.show()
```

## Uso Manual (Avançado)

Se preferir executar ferramentas individualmente:

```bash
# Acessar container
make shell

# Ver ferramentas disponíveis
show-tools

# CK Metrics
ck /workspace/projects/jsoup /output/path

# PMD
pmd check -d /workspace/projects/jsoup/src \
  -R rulesets/java/quickstart.xml -f csv \
  -r /output/pmd-report.csv

# SpotBugs
spotbugs -textui -effort:max \
  -pluginList /tools/spotbugs/plugin/findsecbugs-plugin.jar \
  -xml:withMessages -output /output/spotbugs.xml \
  /workspace/projects/jsoup/target/*.jar

# RefactoringMiner
java -jar /tools/refactoring-miner/RefactoringMiner.jar \
  -a /workspace/projects/jsoup /output/refactorings.json
```

## Comandos Make

```bash
make help              # Mostra todos os comandos
make build             # Constrói imagem Docker
make up                # Inicia ambiente
make down              # Para ambiente
make shell             # Acessa shell do container
make status            # Status dos containers
make clean             # Remove tudo
make rebuild           # Reconstrói do zero

# Análise
make analyze REPO=owner/repo               # Analisa todas as releases
make analyze-limit REPO=owner/repo LIMIT=N # Analisa N releases
make list-releases REPO=owner/repo         # Lista releases

# Extras
make jupyter           # Jupyter Notebook
make test-tools        # Testa ferramentas
make logs              # Ver logs
make results           # Mostra diretório de resultados
```

## Workflow Completo

```bash
# 1. Setup
make build && make up

# 2. Escolher projeto (≥20 releases)
make list-releases REPO=jhy/jsoup

# 3. Analisar (teste com poucas releases primeiro)
make analyze-limit REPO=jhy/jsoup LIMIT=2

# 4. Se ok, analisar todas
make analyze REPO=jhy/jsoup

# 5. Ver resultados
cat workspace/results/jsoup/analysis-summary.txt

# 6. Análise estatística
make jupyter
# Use Python/pandas para processar CSVs

# 7. Identificar melhorias
# Analise métricas altas (WMC, CBO, LCOM)
# Revise bugs do SpotBugs

# 8. Pull Requests
# Fork → Clone → Branch → Fix → PR
```

## Troubleshooting

**Container não inicia:**
```bash
make clean && make build && make up
```

**Análise falha:**
```bash
make logs
# Verifique erros de compilação
```

**Erro git "dubious ownership":**
```bash
# Já configurado automaticamente no script
# Se persistir, entre no container:
make shell
git config --global --add safe.directory /workspace/projects/<projeto>
```

**Problemas de memória:**
Edite `docker-compose.yml`:
```yaml
environment:
  - JAVA_OPTS=-Xmx8g  # Aumentar para 8GB
```

## Próximos Passos

1. ✅ Setup do ambiente
2. ✅ Análise automatizada
3. ⬜ Processamento de dados (Python/Jupyter)
4. ⬜ Análise estatística descritiva
5. ⬜ Identificação de melhorias
6. ⬜ Submissão de PRs (3+)
7. ⬜ Artigo científico
8. ⬜ Upload no Zenodo
9. ⬜ Apresentação

## Recursos

- **CK Metrics:** https://github.com/mauricioaniche/ck
- **SpotBugs:** https://spotbugs.github.io/
- **RefactoringMiner:** https://github.com/tsantalis/RefactoringMiner
- **README completo:** `README.md`

---

**Dúvidas?** Consulte o README.md ou documentação das ferramentas.
