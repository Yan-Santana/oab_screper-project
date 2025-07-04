"""
Testes para o agente LLM
"""

import pytest
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.append(str(Path(_file_).parent.parent / "agent"))

from oab_tool import OABSearchTool
from llm_agent import OABAgent, MockLLM

def test_mock_llm():
    """Testar Mock LLM"""
    llm = MockLLM()
    
    # Teste básico
    response = llm.invoke("Olá")
    assert isinstance(response, str)
    assert len(response) > 0

def test_oab_search_tool_init():
    """Testar inicialização da ferramenta OAB"""
    tool = OABSearchTool()
    
    assert tool.name == "oab_search"
    assert "advogados" in tool.description.lower()
    assert tool.api_base_url == "http://localhost:8000"

def test_oab_agent_init():
    """Testar inicialização do agente"""
    agent = OABAgent(llm_provider="mock")
    
    assert agent.llm_provider == "mock"
    assert len(agent.tools) == 1
    assert agent.tools[0].name == "oab_search"

def test_oab_agent_query():
    """Testar consulta do agente"""
    agent = OABAgent(llm_provider="mock")
    
    # Teste com pergunta simples
    response = agent.query("Como posso ajudá-lo?")
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_oab_tool_error_handling():
    """Testar tratamento de erros da ferramenta"""
    tool = OABSearchTool(api_base_url="http://localhost:9999")  # Porta inexistente
    
    # Deve retornar erro de conexão
    result = tool._run("Teste", "SP")
    assert "Erro" in result or "erro" in result.lower()