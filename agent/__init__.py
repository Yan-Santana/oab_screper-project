'''
OAB Agent - Agente para buscar informações de advogados no site da OAB

Este oacite tem o agente LLm com LangChain p consultas
sobre advogados usando dados daa OAB.
'''

from .llm_agent import OABAgent
from .oab_tool import OABSearchTool

__version__ = "0.1.0"
__all__ = ["OABAgent", "OABSearchTool"]