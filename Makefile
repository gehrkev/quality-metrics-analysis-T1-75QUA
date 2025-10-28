.PHONY: build up down shell logs clean help jupyter test-tools

# Cores para output
GREEN=\033[0;32m
NC=\033[0m # No Color

help: ## Mostra esta mensagem de ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-15s${NC} %s\n", $$1, $$2}'

build: ## Constrói a imagem Docker
	@echo "${GREEN}Construindo imagem Docker...${NC}"
	docker-compose build

up: ## Inicia o ambiente
	@echo "${GREEN}Iniciando ambiente...${NC}"
	docker-compose up -d qualidade-software

down: ## Para o ambiente
	@echo "${GREEN}Parando ambiente...${NC}"
	docker-compose down

shell: ## Acessa o shell do container
	@echo "${GREEN}Acessando shell do container...${NC}"
	docker-compose exec qualidade-software bash

jupyter: ## Inicia Jupyter Notebook
	@echo "${GREEN}Iniciando Jupyter Notebook em http://localhost:8888${NC}"
	docker-compose up -d jupyter

logs: ## Mostra logs do container
	docker-compose logs -f qualidade-software

clean: ## Remove containers e volumes
	@echo "${GREEN}Limpando containers e volumes...${NC}"
	docker-compose down -v
	docker system prune -f

test-tools: ## Testa se todas as ferramentas estão instaladas
	@echo "${GREEN}Testando ferramentas...${NC}"
	docker-compose exec qualidade-software bash -c "\
		echo 'Java:' && java -version && \
		echo '' && echo 'Maven:' && mvn -version && \
		echo '' && echo 'Python:' && python3 --version && \
		echo '' && echo 'Git:' && git --version && \
		echo '' && echo 'CK Tool:' && ls -lh /tools/ck/ck.jar && \
		echo '' && echo 'SpotBugs:' && ls -lh /tools/spotbugs/bin/spotbugs && \
		echo '' && echo 'RefactoringMiner:' && ls -lh /tools/refactoring-miner/RefactoringMiner.jar && \
		echo '' && echo '${GREEN}Todas as ferramentas instaladas!${NC}'"

rebuild: clean build up ## Reconstrói e reinicia o ambiente

status: ## Mostra status dos containers
	docker-compose ps

# Comandos de análise
analyze: ## Analisa um projeto GitHub (uso: make analyze REPO=owner/repo)
	@$(if $(REPO),,$(error Uso: make analyze REPO=owner/repo (ex.: REPO=jhy/jsoup)))
	@echo "${GREEN}Analisando todas as releases de $(REPO)...${NC}"
	docker-compose up -d qualidade-software
	docker-compose exec qualidade-software analyze-all-releases $(REPO)

analyze-limit: ## Analisa com limite (uso: make analyze-limit REPO=owner/repo LIMIT=5)
	@$(if $(and $(REPO),$(LIMIT)),,$(error Uso: make analyze-limit REPO=owner/repo LIMIT=N (ex.: REPO=jhy/jsoup LIMIT=5)))
	@echo "${GREEN}Analisando $(LIMIT) releases de $(REPO)...${NC}"
	docker-compose up -d qualidade-software
	docker-compose exec qualidade-software analyze-all-releases $(REPO) --limit $(LIMIT)

list-releases: ## Lista releases de um projeto (uso: make list-releases REPO=owner/repo)
	@$(if $(REPO),,$(error Uso: make list-releases REPO=owner/repo))
	docker-compose up -d qualidade-software
	docker-compose exec qualidade-software fetch-github-releases $(REPO)

results: ## Mostra o diretório de resultados
	@echo "${GREEN}Abrindo diretório de resultados...${NC}"
	@ls -la workspace/results/ || echo "Nenhum resultado ainda"

# Atalhos úteis
start: up ## Alias para 'up'
stop: down ## Alias para 'down'
bash: shell ## Alias para 'shell'
