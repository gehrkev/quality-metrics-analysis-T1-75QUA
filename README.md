# Ambiente Docker - Trabalho de Qualidade de Software (75QUA)

Ambiente Docker padronizado para análise de qualidade de software em projetos Java, desenvolvido para o trabalho da disciplina 75QUA - UDESC Alto Vale.

## 📋 Ferramentas Incluídas

O ambiente contém todas as ferramentas necessárias para o trabalho:

### Análise de Métricas CK
- **CK Tool** (compilado do source) - Extração de métricas CK
  - Métricas: WMC, DIT, NOC, CBO, LCOM, RFC, LOC
- **PMD** (v7.7.0) - Análise estática de código

### Detecção de Defeitos
- **SpotBugs** (v4.8.6) - Detecção de bugs gerais
- **Find Security Bugs** (v1.13.0) - Plugin para bugs de segurança

### Análise de Refatorações
- **RefactoringMiner** (v3.0.9) - Detecção de refatorações

### Ferramentas de Suporte
- **Java 17** (OpenJDK) - Versão única para todas as ferramentas
- **Maven** & **Gradle**
- **Python 3** com pyDriller, pandas, matplotlib, seaborn
- **Git**
- **Jupyter Notebook** (opcional)

## 🚀 Início Rápido

### Pré-requisitos
- Docker instalado
- Docker Compose instalado

### 1. Construir a Imagem

```bash
docker-compose build
```

### 2. Iniciar o Ambiente

```bash
docker-compose up -d qualidade-software
```

### 3. Acessar o Container

```bash
docker-compose exec qualidade-software bash
```

### 4. Ver Ferramentas Disponíveis

Dentro do container, execute:
```bash
show-tools
```

## 📁 Estrutura de Diretórios

```
75QUA/
├── Dockerfile
├── docker-compose.yml
├── README.md
└── workspace/              # Diretório compartilhado com o container
    ├── projetos/           # Clone seus projetos aqui
    ├── resultados/         # Resultados das análises
    └── scripts/            # Scripts de automação
```

## 🔧 Uso das Ferramentas

### 1. Métricas CK

```bash
# Clonar projeto Java
cd /workspace
git clone <url-do-projeto>

# Executar análise CK
ck /workspace/projeto /workspace/resultados/ck-metrics
```

**Saída:** Arquivos CSV com métricas WMC, DIT, NOC, CBO, LCOM, RFC, LOC

**Nota:** O comando `ck` é um wrapper simplificado para executar o CK Tool.

### 2. SpotBugs (Detecção de Bugs)

```bash
# Primeiro, compile o projeto
cd /workspace/projeto
mvn clean package -DskipTests

# Executar SpotBugs com find-sec-bugs
spotbugs -textui \
  -effort:max \
  -pluginList /tools/spotbugs/plugin/findsecbugs-plugin.jar \
  -xml:withMessages \
  -output /workspace/resultados/spotbugs-report.xml \
  target/*.jar
```

### 3. RefactoringMiner

```bash
# Analisar todas as refatorações do repositório
java -jar /tools/refactoring-miner/RefactoringMiner.jar \
  -a /workspace/projeto \
  /workspace/resultados/refactorings.json
```

### 4. PyDriller (Análise de Releases)

Crie um script Python (`/workspace/scripts/analyze_releases.py`):

```python
from pydriller import Repository
import pandas as pd

# Exemplo: listar todas as tags/releases
repo_path = '/workspace/projeto'
releases = []

for commit in Repository(repo_path, only_releases=True).traverse_commits():
    releases.append({
        'tag': commit.branches,
        'hash': commit.hash,
        'date': commit.committer_date,
        'author': commit.author.name
    })

df = pd.DataFrame(releases)
df.to_csv('/workspace/resultados/releases.csv', index=False)
print(f"Total de releases encontradas: {len(releases)}")
```

Execute:
```bash
python3 /workspace/scripts/analyze_releases.py
```

### 5. PMD

```bash
pmd check \
  -d /workspace/projeto/src \
  -R rulesets/java/quickstart.xml \
  -f csv \
  -r /workspace/resultados/pmd-report.csv
```

## 📊 Jupyter Notebook (Opcional)

Para análise de dados e geração de gráficos:

```bash
# Iniciar Jupyter
docker-compose up -d jupyter

# Acessar em http://localhost:8888
```

## 🔄 Workflow Sugerido

1. **Clone do Projeto**
   ```bash
   cd workspace
   git clone <url-projeto-java>
   ```

2. **Identificar Releases**
   ```bash
   cd projeto
   git tag --list
   ```

3. **Criar Script de Análise Automatizada**
   - Iterar sobre cada release
   - Fazer checkout da release
   - Executar todas as ferramentas
   - Salvar resultados em CSV/JSON

4. **Análise Estatística**
   - Usar Python/Jupyter para processar dados
   - Gerar gráficos de evolução
   - Calcular estatísticas descritivas

5. **Pull Requests**
   - Identificar melhorias no código
   - Criar branches e submeter PRs

## 💡 Dicas

### Cache de Dependências
O docker-compose já configura volumes para cache do Maven e Gradle, acelerando builds subsequentes.

### Memória Java
Por padrão, a JVM está configurada com 4GB. Ajuste conforme necessário no `docker-compose.yml`:
```yaml
environment:
  - JAVA_OPTS=-Xmx8g  # Para 8GB
```

### Compilação do Projeto
Diferentes projetos podem usar Maven ou Gradle:

```bash
# Maven
mvn clean compile package

# Gradle
gradle clean build
```

### Análise de Release Específica

```bash
# Checkout de uma release
git checkout tags/v1.0.0

# Execute as análises
# ...

# Voltar para main
git checkout main
```

## 🛠️ Scripts de Automação

Exemplo de script para analisar múltiplas releases (`workspace/scripts/analyze_all_releases.sh`):

```bash
#!/bin/bash

PROJECT_DIR="/workspace/projeto"
RESULTS_DIR="/workspace/resultados"

cd $PROJECT_DIR

# Listar todas as tags
tags=$(git tag -l)

for tag in $tags; do
    echo "Analisando release: $tag"

    # Checkout da tag
    git checkout $tag

    # Criar diretório para resultados desta release
    mkdir -p "$RESULTS_DIR/$tag"

    # Compilar projeto
    mvn clean package -DskipTests

    # CK Metrics
    ck $PROJECT_DIR "$RESULTS_DIR/$tag/ck"

    # SpotBugs
    spotbugs -textui -effort:max \
        -pluginList /tools/spotbugs/plugin/findsecbugs-plugin.jar \
        -xml:withMessages \
        -output "$RESULTS_DIR/$tag/spotbugs.xml" \
        target/*.jar

    echo "Análise de $tag concluída"
done

# Voltar para main
git checkout main
echo "Todas as análises concluídas!"
```

## 🐛 Troubleshooting

### Container não inicia
```bash
# Ver logs
docker-compose logs qualidade-software

# Reconstruir imagem
docker-compose build --no-cache
```

### Ferramentas não encontradas
```bash
# Verificar se as ferramentas foram instaladas
ls -la /tools/
```

### Problemas de memória
Aumente a memória do Docker Desktop (macOS/Windows) ou ajuste JAVA_OPTS.

## 📦 Comandos Úteis

```bash
# Parar containers
docker-compose down

# Remover volumes (limpar cache)
docker-compose down -v

# Ver containers em execução
docker ps

# Entrar no container em execução
docker exec -it 75qua-ambiente bash

# Copiar arquivos do container para host
docker cp 75qua-ambiente:/workspace/resultados ./resultados-local
```

## 👥 Colaboração

Todos os membros do grupo podem usar o mesmo ambiente:

1. Compartilhe o repositório com Dockerfile e docker-compose.yml
2. Cada membro executa `docker-compose build` localmente
3. Use Git para compartilhar scripts e coordenar análises
4. Sincronize a pasta `workspace/` via Git (adicione ao .gitignore arquivos grandes)

## 📄 Licença

Este ambiente foi criado para fins educacionais - Trabalho da disciplina 75QUA, UDESC Alto Vale.

---

**Desenvolvido para:** Bacharelado em Engenharia de Software - UDESC Alto Vale
**Disciplina:** 75QUA - Qualidade de Software
**Professor:** Paulo Roberto Farah
