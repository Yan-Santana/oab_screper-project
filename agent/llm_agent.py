import os
import re
import requests
import json
from typing import List, Optional, Dict, Any, Union
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from .oab_tool import OABSearchTool
import logging

# Config logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class OABAgent:
    ''' Um Agente LLM para consultas sobre advogados na OAB '''
    
    def __init__(self, api_base_url: str = None, llm_provider: str = "openai"):
        ''' Inicializa o agente. 
        Args:
            api_base_url: URL base da API do scraper
            llm_provider: 'openai', 'ollama' ou pode ser o 'mock'
        '''
        # Usar variável de ambiente se não fornecida
        self.api_base_url = api_base_url or os.getenv("SCRAPER_API_URL", "http://scraper-api:8000")
        self.llm_provider = llm_provider

        # Iniciar ferramentas
        self.tools = [OABSearchTool(api_base_url=self.api_base_url)]
        
        # Iniciar a LLM
        self.llm = self._setup_llm()
        
        # Criar o prompt template
        self.prompt = self._create_prompt()
        
        # Criar o nossso agente 
        self.agent = self._create_agent()
        
    def _setup_llm(self):
        ''' Config o modelo de linguagem escolhido '''
        logger.info(f"Configurando LLM com provedor: {self.llm_provider}")
        
        if self.llm_provider == "openai":
            # Configuração para OpenAI padrão
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            
            logger.info(f"OpenAI API Key configurada: {api_key[:20]}..." if api_key else "NÃO configurada")
            logger.info(f"OpenAI Model: {model}")
            
            if not api_key:
                logger.warning("OPENAI_API_KEY não configurada. Usando mock LLM.")
                return MockLLM()
            
            try:
                llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,
                    max_tokens=1000,
                    openai_api_key=api_key
                )
                logger.info("✅ ChatOpenAI configurado com sucesso!")
                return llm
            except Exception as e:
                logger.error(f"Erro ao configurar ChatOpenAI: {e}")
                logger.warning("Usando MockLLM como fallback")
                return MockLLM()
        elif self.llm_provider == "cloudflare_openai":
            # Configuração para OpenAI via Cloudflare
            api_key = os.getenv("OPENAI_API_KEY", "cf_dummy_key")
            api_base = os.getenv("OPENAI_API_BASE")
            cf_token = os.getenv("CF_API_TOKEN")
            
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "@cf/tinyllama/tinyllama-1.1b-chat-v1.0"),
                temperature=0.1,
                max_tokens=1000,
                openai_api_key=api_key,
                openai_api_base=api_base,
                default_headers={"Authorization": f"Bearer {cf_token}"} if cf_token else {}
            )
        elif self.llm_provider == "ollama":
            return Ollama(model="llama2",
                          temperature=0.1)
        elif self.llm_provider == "cloudflare":
            return CloudflareLLM()
        else:
            return MockLLM() # Para testes local
    
    def _create_prompt(self) -> PromptTemplate:
        ''' Cria o prompt para o agente '''
        template = """
You are an assistant that must strictly follow the ReAct format below to answer questions about Brazilian lawyers (OAB):

Question: {input}
Thought: <your reasoning>
Action: oab_search
Action Input: {{"name": "<full name>", "uf": "<UF>"}}
Observation: <result of the search>
Thought: Now I know the final answer.
Final Answer: <final answer in Portuguese>

IMPORTANT:
- Always use the Action/Action Input/Observation steps, do not skip or change the format.
- Do not answer directly, always use the tool.
- If you do not have enough information, ask for the full name and UF.
- After receiving the Observation, always proceed to the Final Answer. Do not repeat the Action step.
- Always provide the Final Answer in Portuguese.

Example:
Question: What is the OAB number of João Silva from SP?
Thought: I need to search for João Silva in SP.
Action: oab_search
Action Input: {{"name": "João Silva", "uf": "SP"}}
Observation: {{"oab": "123456", "name": "João Silva", "uf": "SP", "categoria": "Advogado", "data_inscricao": "01/01/2000", "situacao": "Ativo"}}
Thought: Now I know the final answer.
Final Answer: O número da OAB de João Silva (SP) é 123456. Situação: Ativo.

Question: {input}
{agent_scratchpad}
{tools}
{tool_names}
"""
        return PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
        )
    
    def _create_agent(self) -> AgentExecutor:
        ''' Cria o agente Executor'''
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Criar o executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,  # Habilitar verbose para debug
            handle_parsing_errors=True,
            max_iterations=20,
        )
        return agent_executor

    def query(self, question: str) -> str:
        """
        Vai processar a consulta sobre o advogado.
        Args:
            question: A pergunta do usuário em português
        Returns:
            A resposta do agente
        """
        try:
            # Executa o agente
            result = self.agent.invoke({"input": question})
            
            # Extrair resposta
            response = result.get("output", "Não foi possível processar a pergunta")
            
            return response
        except Exception as e:
            return f"Desculpe, ocorreu um erro ao processar a pergunta: {str(e)}"


class CloudflareLLM:
    """LLM usando Cloudflare Workers AI"""
    
    def __init__(self):
        from config import Config
        self.account_id = Config.CF_ACCOUNT_ID
        self.api_token = Config.CF_API_TOKEN
        self.model = Config.CF_MODEL
        self.temperature = 0.1
        
        if not self.account_id or not self.api_token:
            raise ValueError("CF_ACCOUNT_ID e CF_API_TOKEN são obrigatórios para usar Cloudflare Workers AI")
    
    def invoke(self, prompt: Union[str, Any]) -> str:
        """Invoca o modelo Cloudflare Workers AI"""
        # Se for objeto StringPromptValue, extrai o texto
        if not isinstance(prompt, str):
            if hasattr(prompt, 'text'):
                prompt_text = prompt.text
            elif hasattr(prompt, 'value'):
                prompt_text = prompt.value
            else:
                prompt_text = str(prompt)
        else:
            prompt_text = prompt
        
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {"role": "system", "content": "You are a friendly assistant"},
                    {"role": "user", "content": prompt_text}
                ],
                "temperature": 0.1
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get("success") and result.get("result"):
                return result["result"]["response"]
            else:
                logger.error(f"Erro na resposta do Cloudflare: {result}")
                return "Erro ao processar resposta do Cloudflare Workers AI"
                
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta detalhada do Cloudflare: {e.response.text}")
                logger.error(f"Status code: {e.response.status_code}")
            logger.error(f"Erro na requisição para Cloudflare: {e}")
            return f"Erro de conexão com Cloudflare Workers AI: {str(e)}"
        except Exception as e:
            logger.error(f"Erro inesperado no Cloudflare LLM: {e}")
            return f"Erro inesperado: {str(e)}"
    
    def __call__(self, prompt: Union[str, Any]) -> str:
        return self.invoke(prompt)

    def bind(self, **kwargs):
        """Garante compatibilidade com a interface esperada pelo LangChain"""
        return self


class MockLLM: 
    """Mock LLM para testes quando nao tenho acesso ao modelo real"""
    def __init__(self):
        self.temperature = 0.1
    
    def invoke(self, prompt: Union[str, Any]) -> str:
        """Simula uma resposta do LLM, aceita string ou StringPromptValue, e responde no formato esperado pelo LangChain."""
        # Se for objeto StringPromptValue, extrai o texto
        if not isinstance(prompt, str):
            if hasattr(prompt, 'text'):
                prompt_text = prompt.text
            elif hasattr(prompt, 'value'):
                prompt_text = prompt.value
            else:
                prompt_text = str(prompt)
        else:
            prompt_text = prompt

        # Se já houve uma observação, retorne a resposta final
        if "Observation:" in prompt_text:
            return "Thought: Agora posso fornecer a resposta final\nFinal Answer: Aqui estão os dados simulados do advogado solicitado. ✅"
        # Se acabou de executar uma ação, retorne uma observação
        if "Action Input:" in prompt_text:
            return "Observation: [Resultado simulado da busca na OAB]"

        # Tenta extrair nome e UF de frases livres
        name = None
        uf = None
        # Busca por "nome: ..." e "uf: ..."
        name_match = re.search(r'nome[:\s]+([A-Za-zÀ-ÿ\s]+)', prompt_text, re.IGNORECASE)
        uf_match = re.search(r'uf[:\s]+([A-Z]{2})', prompt_text, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
        # Busca "advogado ... na UF XX"
        adv_match = re.search(r'advogado ([A-Za-zÀ-ÿ\s]+) na UF ([A-Z]{2})', prompt_text, re.IGNORECASE)
        if adv_match:
            name = adv_match.group(1).strip()
            uf = adv_match.group(2).strip()
        elif uf_match:
            uf = uf_match.group(1).strip()

        if (name and uf):
            return (
                f"Thought: Preciso buscar informações sobre o advogado {name} na UF {uf}\n"
                f"Action: oab_search\n"
                f"Action Input: {{\"name\": \"{name}\", \"uf\": \"{uf}\"}}"
            ).replace('{{', '{').replace('}}', '}')
        elif (name or uf):
            return (
                "Thought: Preciso de mais informações para buscar o advogado\n"
                "Final Answer: Para buscar um advogado, você precisa do nome completo e da UF/Seccional"
            )
        elif ("buscar" in prompt_text.lower() or "consultar" in prompt_text.lower()):
            return (
                "Thought: Preciso de mais informações para buscar o advogado\n"
                "Final Answer: Para buscar um advogado, você precisa do nome completo e da UF/Seccional"
            )
        return "Final Answer: Como posso ajudá-lo com consultas sobre advogados da OAB?"
    
    def __call__(self, prompt: Union[str, Any]) -> str:
        return self.invoke(prompt)

    def bind(self, **kwargs):
        """ Garanti compatibilidade com a interface esperada pelo LangChain.."""
        return self
