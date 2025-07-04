# OAB Scraper com OpenAI - Configuração

Este guia explica como configurar e executar o OAB Scraper com o agente LLM usando OpenAI.

## 🚀 Configuração Rápida

### 1. Configurar OpenAI API Key

Primeiro, você precisa de uma chave da API do OpenAI:

1. Acesse [OpenAI Platform](https://platform.openai.com/api-keys)
2. Crie uma nova API key
3. Copie a chave (começa com `sk-`)

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# Configurações do LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-sua-chave-aqui
OPENAI_MODEL=gpt-3.5-turbo

# Configurações gerais
MAX_ITERATIONS=5
TIMEOUT=120
VERBOSE=true
LOG_LEVEL=INFO
HEADLESS=true
BROWSER_TIMEOUT=120000
```

### 4. Testar o Sistema

Após iniciar, você pode testar:

```bash
# Testar consulta direta
TESTE 1 - COM LOG (COM ADVOGADO REAL):
   docker exec oab-llm-agent python main.py query "Qual o número da OAB de LUIZ CARLOS BENEDITO HORMUNG do MS?" --llm-provider openai

TESTE 2 - SEM LOG (COM ADVOGADO REAL):
     docker exec oab-llm-agent python main.py query "Qual o número da OAB de LUIZ CARLOS BENEDITO HORMUNG do MS?" --llm-provider openai 2>/dev/null | grep -vE 'INFO:|DEBUG:|WARNING:|Entering new AgentExecutor chain|Finished chain'

TESTE 3 - SEM LOG (NAO ENCONTRADO)
	docker exec oab-llm-agent python main.py query "Qual o número da OAB de fulano de tal do MS?" --llm-provider openai 2>/dev/null | grep -vE 'INFO:|DEBUG:|WARNING:|Entering new AgentExecutor chain|Finished chain'

TESTE 4 - SEM LOG (COM ADVOGADO REAL):
     docker exec oab-llm-agent python main.py query "Busque informações sobre Carlos Oliveira no RJ" --llm-provider openai 2>/dev/null | grep -vE 'INFO:|DEBUG:|WARNING:|Entering new AgentExecutor chain|Finished chain'

# Testar a API do scraper
curl -X POST "http://localhost:8000/fetch_oab" \
  -H "Content-Type: application/json" \
  -d '{"name": "João Silva", "uf": "SP"}'
```

### 5. Executar Manualmente

Se preferir executar manualmente:

```bash
# Parar containers existentes
docker-compose down

# Construir e iniciar
docker-compose up --build
```

## 🔧 Configurações Avançadas

### Modelos Disponíveis

- `gpt-3.5-turbo` (padrão, mais rápido e econômico)
- `gpt-4` (mais preciso, mas mais caro)
- `gpt-4-turbo` (equilibrio entre precisão e custo)

### Configurações de Performance

```bash
# Aumentar iterações para consultas complexas
MAX_ITERATIONS=10

# Aumentar timeout para consultas demoradas
TIMEOUT=300

# Habilitar logs detalhados
VERBOSE=true
LOG_LEVEL=DEBUG
```

## 🐛 Solução de Problemas

### Container LLM Agent sai imediatamente

**Problema**: O container `llm-agent` sai com código 0

**Solução**:

1. Verifique se a `OPENAI_API_KEY` está configurada corretamente
2. Verifique se a chave é válida
3. Verifique os logs: `docker-compose logs llm-agent`

### Erro de autenticação OpenAI

**Problema**: Erro 401 ou 403 da API OpenAI

**Solução**:

1. Verifique se a API key está correta
2. Verifique se tem créditos na conta OpenAI
3. Verifique se o modelo especificado está disponível

### Container não inicia

**Problema**: Erro ao construir ou iniciar containers

**Solução**:

1. Verifique se o Docker está rodando
2. Execute `docker-compose down` e depois `docker-compose up --build`
3. Verifique se as portas 8000 e 8001 estão livres

## 📊 Monitoramento

### Logs dos Containers

```bash
# Logs do scraper API
docker-compose logs scraper-api

# Logs do agente LLM
docker-compose logs llm-agent

# Logs de ambos
docker-compose logs -f
```

### Endpoints Disponíveis

- **API Scraper**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Monitoramento de Uso

1. Acesse [OpenAI Usage](https://platform.openai.com/usage)
2. Configure alertas de uso
3. Monitore os logs do container para ver o consumo

## 🔄 Alternativas

Se não quiser usar OpenAI, você pode usar:

1. **Mock LLM** (para testes): `LLM_PROVIDER=mock`
2. **Cloudflare Workers AI**: Configure `CF_ACCOUNT_ID` e `CF_API_TOKEN`
3. **Ollama** (local): Instale Ollama e configure `LLM_PROVIDER=ollama`

## 📝 Exemplo de Uso

Após iniciar o sistema:

```bash
# Testar a API
curl -X POST "http://localhost:8000/fetch_oab" \
  -H "Content-Type: application/json" \
  -d '{"name": "João Silva", "uf": "SP"}'

# O agente LLM estará disponível interativamente
# Você pode fazer perguntas como:
# "Qual o número da OAB de Maria Santos de SP?"
# "Busque informações sobre Carlos Oliveira no RJ"
```
