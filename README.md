# Ambiente Docker - Trabalho de Qualidade de Software (75QUA)

Ambiente Docker automatizado para análise de qualidade de software em projetos Java, desenvolvido para o trabalho da disciplina 75QUA - Qualidade de Software - UDESC Alto Vale. \
Inicialmente utilizado na análise da biblioteca [jhy/jsoup](https://github.com/jhy/jsoup), com artigo e resultados disponibilizados no Zenodo [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17625604.svg)](https://doi.org/10.5281/zenodo.17625604)


## 📋 Ferramentas Incluídas

- **[CK](https://github.com/mauricioaniche/ck)** (v0.7.0) - Métricas CK (WMC, DIT, NOC, CBO, LCOM, RFC, LOC)
- **[PMD](https://github.com/pmd/pmd)** (v7.7.0) - Análise estática de código
- **[SpotBugs](https://github.com/spotbugs/spotbugs)** (v4.8.6) + **[Find Security Bugs](https://github.com/find-sec-bugs/find-sec-bugs/)** (v1.13.0) - Detecção de bugs e vulnerabilidades
- **[RefactoringMiner](https://github.com/tsantalis/RefactoringMiner)** (v3.0.9) - Detecção de refatorações
- **Java 11 (Padrão)** (OpenJDK), **Maven**, **Gradle**, **Git**
- **Java 17** (OpenJDK) - Wrapper usado pelo RefactoringMiner
- **Python 3** com pyDriller, pandas, matplotlib, seaborn
- **Jupyter Notebook** (opcional)

## 🚀 Início Rápido

> **Quer começar rápido?** Veja [QUICKSTART.md](QUICKSTART.md) para um guia de 5 minutos.

### Pré-requisitos
- Docker e Docker Compose instalados
- Make (opcional, mas recomendado)

> **Usando Colima?** Veja [COLIMA_NOTES.md](COLIMA_NOTES.md) para dicas específicas de configuração e troubleshooting.

### 1. Construir e Iniciar

```bash
make build && make up
```

Ou sem Make:
```bash
docker-compose build
docker-compose up -d qualidade-software
```

### 2. Analisar um Projeto Java

**Análise completa de todas as releases:**
```bash
make analyze REPO=jhy/jsoup
```

**Análise limitada (ex: primeiras 5 releases):**
```bash
make analyze-limit REPO=jhy/jsoup LIMIT=5
```

**Listar releases disponíveis:**
```bash
make list-releases REPO=jhy/jsoup
```

### 3. Ver Resultados

Os resultados são salvos em `workspace/results/<projeto>/`:
```bash
ls -la workspace/results/jsoup/
```

Cada release gera:
- `ck/` - 4 arquivos CSV com métricas CK (class, method, field, variable)
- `pmd-report.csv` - Relatório PMD
- `pmd.log` - Logs do PMD
- `spotbugs-report.xml` - Relatório SpotBugs
- `spotbugs.log` - Logs do SpotBugs
- `metadata.json` - Metadados da release
- `summary.json` - Resumo dos resultados

Relatório geral: `workspace/results/<projeto>/analysis-summary.txt`

RefactoringMiner (repositório completo):
- `workspace/results/<projeto>/refactorings-all.json` – refatorações detectadas
- `workspace/results/<projeto>/refactoring-miner.log` – log (stdout/erros)

## 📁 Estrutura de Diretórios

```
75QUA/
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── README.md
├── scripts/                    # Scripts para o container
│   ├── analyze_all_releases.py
│   ├── fetch_github_releases.py
│   └── entrypoint.sh
└── workspace/                  # Volume compartilhado
    ├── projects/               # Repositórios clonados
    └── results/                # Resultados das análises
```

## 🔧 Comandos Make Disponíveis

```bash
make help              # Mostra todos os comandos
make build             # Constrói a imagem Docker
make up                # Inicia o ambiente
make down              # Para o ambiente
make shell             # Acessa o shell do container
make status            # Status dos containers
make clean             # Remove containers e volumes
make rebuild           # Reconstrói tudo do zero

# Análise
make analyze REPO=owner/repo               # Analisa todas as releases
make analyze-limit REPO=owner/repo LIMIT=N # Analisa N releases
make list-releases REPO=owner/repo         # Lista releases disponíveis
make results                               # Mostra resultados

# Extras
make jupyter           # Inicia Jupyter Notebook (localhost:8888)
make notebook          # Abre notebook de análise de métricas
make test-tools        # Testa se ferramentas estão instaladas
make clean-results     # Remove apenas resultados (mantém containers)
```

## 🔄 Workflow Automatizado

O script `analyze-all-releases` executa automaticamente:

1. ✅ Busca releases do GitHub (via API)
2. ✅ Clona/atualiza o repositório
3. ✅ Para cada release:
   - Faz checkout da tag
   - Compila o projeto (Maven/Gradle)
   - Executa CK Metrics
   - Executa PMD
   - Executa SpotBugs + find-sec-bugs
4. ✅ Executa RefactoringMiner no repositório completo
5. ✅ Gera relatório resumido

**Exemplo de saída:**
```
============================================================
Buscando releases de jhy/jsoup...
============================================================
✓ Encontradas 20 releases

[1/20]
────────────────────────────────────────────────────────────
Analisando: jsoup-1.12.2 (2020-02-09)
────────────────────────────────────────────────────────────
  → Checkout jsoup-1.12.2
  → Compilando projeto...
    ✓ Compilação concluída
  → Executando CK Metrics...
    ✓ CK Metrics salvo (4 arquivos)
  → Executando PMD...
    ✓ PMD report salvo
  → Executando SpotBugs...
    ✓ SpotBugs report salvo
```

## 📊 Análise de Dados

### Notebook de Análise Completo (Recomendado)

Um notebook Jupyter pronto com todas as análises:

```bash
make notebook
# Acesse: http://localhost:8888/notebooks/scripts/analyze_metrics.ipynb
```

**O notebook inclui:**
- ✅ Métricas CK (WMC, DIT, NOC, CBO, LCOM, RFC, LOC)
- ✅ Análise PMD (problemas de código por prioridade)
- ✅ Bugs SpotBugs (gerais, segurança, críticos)
- ✅ Refatorações (RefactoringMiner)
- ✅ Análises avançadas:
  - Top 10 arquivos/classes mais refatorados
  - Categorização de refatorações
  - Cruzamento com métricas CK
  - Estatísticas descritivas
- ✅ Gráficos prontos (evolução, boxplots, heatmaps)
- ✅ Exportação automática de CSVs e PNGs

## 💡 Uso Avançado

### Acesso ao Container

```bash
make shell
# Agora você está dentro do container
```

### Uso Manual das Ferramentas

Se preferir usar as ferramentas separadamente:

**CK Metrics:**
```bash
ck /workspace/projects/jsoup /workspace/results/ck-output
```

**PMD:**
```bash
pmd check -d /workspace/projects/jsoup/src \
  -R rulesets/java/quickstart.xml -f csv \
  -r /workspace/results/pmd-report.csv
```

**SpotBugs:**
```bash
spotbugs -textui -effort:max \
  -pluginList /tools/spotbugs/plugin/findsecbugs-plugin.jar \
  -xml:withMessages -output /workspace/results/spotbugs.xml \
  /workspace/projects/jsoup/target/*.jar
```

**RefactoringMiner (usa Java 17 automaticamente):**
```bash
/tools/refactoring-miner/refactoring-miner.sh \
  -a /workspace/projects/jsoup main -json /workspace/results/refactorings.json
```

**Ver ferramentas disponíveis:**
```bash
show-tools
```

### Análise Personalizada com Python/Jupyter

Para análises customizadas além do notebook pronto:

```bash
make jupyter
# Acesse http://localhost:8888
```

Exemplo de script Python personalizado:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Carregar métricas CK de uma release
df = pd.read_csv('workspace/results/jsoup/jsoup-1.12.2/ck/class.csv')

# Análise
print(f"Total de classes: {len(df)}")
print(f"CBO médio: {df['cbo'].mean():.2f}")
print(f"WMC médio: {df['wmc'].mean():.2f}")

# Gráfico
df['wmc'].hist(bins=30)
plt.xlabel('WMC')
plt.ylabel('Frequência')
plt.show()
```

## 🐛 Troubleshooting

**Container não inicia:**
```bash
make clean && make build && make up
```

**Erro de permissão do Git:**
```bash
docker-compose exec qualidade-software \
  git config --global --add safe.directory /workspace/projects/<projeto>
```

**Ver logs:**
```bash
make logs
```

## 👥 Colaboração

1. Clone o repositório
2. Execute o workflow descrito em [QUICKSTART.md](QUICKSTART.md)
3. Compartilhe a pasta `workspace/results/`

## 📚 Documentação Adicional

- **[QUICKSTART.md](QUICKSTART.md)** - Guia rápido de 5 minutos com workflow completo
- **[COLIMA_NOTES.md](COLIMA_NOTES.md)** - Dicas para usar Docker com Colima no macOS

## 📄 Licença

Ambiente criado para fins educacionais - Trabalho da disciplina 75QUA, UDESC Alto Vale.

---

**Desenvolvido para:** Bacharelado em Engenharia de Software - UDESC Alto Vale \
**Disciplina:** 75QUA - Qualidade de Software \
**Professor:** Paulo Roberto Farah
