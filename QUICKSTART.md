# 🚀 Guia Rápido - Ambiente Docker 75QUA

## Setup Inicial (5 minutos)

### 1. Construir e Iniciar

```bash
# Construir a imagem (primeira vez - ~10min)
make build

# Iniciar o ambiente
make up

# Acessar o shell
make shell
```

### 2. Verificar Instalação

Dentro do container:
```bash
show-tools
```

## Workflow Básico

### Passo 1: Escolher e Clonar Projeto

Dentro do container (`make shell`):

```bash
cd /workspace/projetos

# Exemplo: Apache Commons Lang
git clone https://github.com/apache/commons-lang.git
cd commons-lang

# Verificar número de releases
git tag | wc -l
```

**Requisito:** Projeto deve ter ≥ 20 releases

### Passo 2: Extrair Informações de Releases

```bash
# Usar script Python
python3 /workspace/scripts/extract_releases.py commons-lang
```

**Saída:** `/workspace/resultados/commons-lang/releases.csv`

### Passo 3: Analisar Todas as Releases

```bash
# Executar análise completa
/workspace/scripts/analyze_all_releases.sh commons-lang
```

Este script para cada release:
- Faz checkout
- Compila o projeto
- Extrai métricas CK
- Executa SpotBugs

**Resultado:** Pasta `/workspace/resultados/commons-lang/` com subpastas para cada release

### Passo 4: Analisar Refatorações

```bash
cd /workspace/projetos/commons-lang

# Gerar JSON com todas as refatorações
java -jar /tools/refactoring-miner/RefactoringMiner.jar \
  -a /workspace/projetos/commons-lang \
  /workspace/resultados/commons-lang/refactorings.json
```

### Passo 5: Consolidar e Analisar Dados

Use Python/Jupyter para processar os resultados:

```bash
# No host (fora do container)
make jupyter

# Acesse http://localhost:8888
```

Crie um notebook para:
- Ler CSVs das métricas
- Calcular estatísticas descritivas
- Gerar gráficos de evolução

## Sugestões de Projetos Java

Projetos populares com muitas releases:

1. **Apache Commons Lang** (100+ releases)
   - `https://github.com/apache/commons-lang`
   - Biblioteca de utilitários Java

2. **Apache Commons IO** (40+ releases)
   - `https://github.com/apache/commons-io`
   - Utilitários para I/O

3. **JUnit 5** (100+ releases)
   - `https://github.com/junit-team/junit5`
   - Framework de testes

4. **Gson** (40+ releases)
   - `https://github.com/google/gson`
   - Biblioteca JSON do Google

5. **OkHttp** (100+ releases)
   - `https://github.com/square/okhttp`
   - Cliente HTTP

## Comandos Make Úteis

```bash
make help          # Ver todos os comandos
make build         # Construir imagem
make up            # Iniciar container
make down          # Parar container
make shell         # Acessar shell
make jupyter       # Iniciar Jupyter
make logs          # Ver logs
make test-tools    # Verificar ferramentas
make clean         # Limpar tudo
make rebuild       # Reconstruir do zero
```

## Estrutura de Resultados

```
workspace/resultados/nome-projeto/
├── releases.csv              # Lista de releases (pydriller)
├── releases.json
├── refactorings.json         # Todas as refatorações (RefactoringMiner)
├── v1.0.0/                   # Resultados da release v1.0.0
│   ├── ck/
│   │   ├── class.csv         # Métricas por classe
│   │   ├── method.csv        # Métricas por método
│   │   └── variable.csv      # Métricas por variável
│   ├── spotbugs.xml          # Bugs detectados
│   └── build.log
├── v1.1.0/
│   └── ...
└── metrics_summary.csv       # Consolidação de todas as releases
```

## Análise Estatística Básica

Exemplo de script Python:

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ler métricas de todas as releases
releases = []
for release_dir in Path('/workspace/resultados/projeto').glob('v*'):
    ck_file = release_dir / 'ck' / 'class.csv'
    if ck_file.exists():
        df = pd.read_csv(ck_file)
        df['release'] = release_dir.name
        releases.append(df)

df_all = pd.concat(releases)

# Estatísticas por release
stats = df_all.groupby('release').agg({
    'wmc': ['mean', 'median', 'std'],
    'cbo': ['mean', 'median', 'std'],
    'lcom': ['mean', 'median', 'std'],
    'loc': ['sum', 'mean']
})

# Gráfico de evolução
plt.figure(figsize=(12, 6))
stats['wmc']['mean'].plot(kind='line', marker='o')
plt.title('Evolução do WMC Médio por Release')
plt.xlabel('Release')
plt.ylabel('WMC Médio')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('/workspace/resultados/wmc_evolution.png')
```

## Pull Requests

Após identificar melhorias:

1. **Fork do repositório** no GitHub
2. **Clone do fork** dentro do container
3. **Criar branch** para melhoria
4. **Fazer alterações**
5. **Commit e push**
6. **Criar PR** via interface web do GitHub

Exemplo de melhorias:
- Reduzir complexidade (WMC alto)
- Melhorar coesão (LCOM alto)
- Corrigir bugs de segurança detectados
- Adicionar testes faltantes
- Refatorar código duplicado

## Troubleshooting

### "Comando não encontrado"
```bash
# Reconstruir imagem
make rebuild
```

### "Erro de memória ao compilar"
Edite `docker-compose.yml`:
```yaml
environment:
  - JAVA_OPTS=-Xmx8g  # Aumentar para 8GB
```

### "Git clone muito lento"
Fazer shallow clone:
```bash
git clone --depth 1 --no-single-branch <url>
git fetch --tags
```

### "SpotBugs não encontra JARs"
Certifique-se de compilar com:
```bash
mvn clean package -DskipTests
# ou
gradle clean build -x test
```

## Dicas de Produtividade

1. **Use tmux/screen** dentro do container para múltiplas sessões
2. **Automatize tudo** - crie scripts para tarefas repetitivas
3. **Salve resultados frequentemente** - sincronize workspace/ com Git
4. **Documente achados** - mantenha um NOTES.md no workspace
5. **Divida o trabalho** - cada membro analisa diferentes aspectos

## Próximos Passos

1. ✅ Escolher projeto (≥20 releases)
2. ✅ Extrair lista de releases
3. ✅ Executar análises automatizadas
4. ⬜ Processar dados e gerar gráficos
5. ⬜ Análise estatística descritiva
6. ⬜ Identificar melhorias para PRs
7. ⬜ Submeter 3+ pull requests
8. ⬜ Escrever artigo científico
9. ⬜ Upload para Zenodo
10. ⬜ Preparar apresentação

## Recursos Adicionais

- **CK Metrics:** https://github.com/mauricioaniche/ck
- **SpotBugs:** https://spotbugs.github.io/
- **RefactoringMiner:** https://github.com/tsantalis/RefactoringMiner
- **PyDriller:** https://pydriller.readthedocs.io/

---

**Dúvidas?** Consulte o README.md completo ou entre em contato com o grupo.
