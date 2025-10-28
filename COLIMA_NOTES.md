# Notas sobre uso com Colima

## O que é Colima?

Colima é uma alternativa leve ao Docker Desktop para macOS (e Linux). Ele roda Docker containers em uma VM mínima, sendo:
- Mais leve e rápido
- Gratuito e open-source
- Totalmente compatível com Docker CLI

## Configuração Atual

Seu ambiente está rodando com:
- **Runtime:** Docker via Colima
- **Arquitetura:** ARM64 (Apple Silicon)
- **Virtualização:** macOS Virtualization.Framework
- **Mount Type:** SSHFS

## Comandos Úteis do Colima

```bash
# Ver status
colima status

# Iniciar Colima (se não estiver rodando)
colima start

# Parar Colima
colima stop

# Reiniciar Colima
colima restart

# Ver configuração
colima list

# Aumentar recursos (se necessário)
colima start --cpu 4 --memory 8
```

## Diferenças em Relação ao Docker Desktop

### O que funciona igual:
- ✅ `docker` commands
- ✅ `docker-compose` commands
- ✅ Volumes montados
- ✅ Port forwarding
- ✅ Todos os comandos deste projeto

### Pequenas diferenças:
- ⚠️ Volumes são montados via SSHFS (pode ser um pouco mais lento)
- ⚠️ Alguns avisos podem aparecer (são inofensivos)

## Otimizações para Colima

### 1. Aumentar Recursos (se necessário)

Se o build ou as análises estiverem lentas:

```bash
# Parar Colima
colima stop

# Reiniciar com mais recursos
colima start --cpu 4 --memory 8 --disk 60
```

### 2. Melhorar Performance de Volumes

Se os volumes estiverem lentos, você pode usar virtiofs:

```bash
colima stop
colima start --mount-type virtiofs
```

### 3. Cache de Build

O Colima mantém cache de builds Docker normalmente, então:
- Primeira build: ~10 minutos
- Rebuilds: ~2-3 minutos (se mudar algo no Dockerfile)

## Troubleshooting Específico do Colima

### Problema: "Cannot connect to Docker daemon"

```bash
# Verificar se Colima está rodando
colima status

# Se não estiver, iniciar
colima start
```

### Problema: Build muito lento

```bash
# Ver uso de recursos
colima status

# Aumentar memória/CPU
colima stop
colima start --cpu 4 --memory 8
```

### Problema: Volume não sincroniza arquivos

```bash
# Reiniciar Colima
colima restart

# Ou recriar
colima delete
colima start
```

### Problema: "No space left on device"

```bash
# Aumentar disco
colima stop
colima start --disk 100  # 100GB
```

## Avisos Esperados (pode ignorar)

Ao rodar docker-compose, você pode ver:
- `version attribute is obsolete` - É só um aviso, funciona normalmente
- `buildx isn't installed` - Não é necessário para este projeto

## Vantagens do Colima para Este Projeto

1. **Leve:** Usa menos RAM que Docker Desktop
2. **Rápido:** Inicialização mais rápida
3. **Configurável:** Fácil ajustar recursos
4. **CLI-friendly:** Perfeito para desenvolvimento

## Uso no Grupo

Todos os membros do grupo podem usar:
- **macOS:** Colima (como você) ou Docker Desktop
- **Linux:** Docker nativo
- **Windows:** Docker Desktop ou WSL2

O ambiente Docker é **100% compatível** entre todos!

## Recursos Recomendados

Para análises de projetos grandes (muitas releases):

```bash
colima start --cpu 4 --memory 8 --disk 60
```

Para projetos médios (20-50 releases):

```bash
colima start --cpu 2 --memory 4 --disk 40
```

---

**Tudo funciona igual!** Use todos os comandos do README.md normalmente. 🚀
