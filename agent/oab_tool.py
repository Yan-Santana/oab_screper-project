from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import json
from typing import Optional, Dict, Any, Type
import os
import logging

logging.basicConfig(level=logging.ERROR)

class OABSearchInput(BaseModel): # Modelo para entrada da ferramenta de busca OAB
    name: str = Field(..., description="Nome completo do advogado a ser buscado")
    uf: str = Field(..., description="UF/Seccional do advogado(ex: SP, MS, MG, etc...)")
    
class OABSearchTool(BaseTool): # Ferramenta de busca OAB
    name: str = "oab_search"
    description: str = """
    Util p/ buscar informações de advogados na OAB.
    Recebe o nome completo do advogado e a UF/Seccional.
    Retorna os dados do advogado(OAB, nome, UF, categoria, data de inscrição, situação).
    """
    
    args_schema: Type[BaseModel] = OABSearchInput
    api_base_url: str = "http://scraper-api:8000"
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__()
        self.api_base_url = api_base_url
        
    def _run(self, name: str, uf: str = None) -> str:
        ''' Executa a busca na API do scraper '''
        
        # Corrige caso o campo 'name' venha como um JSON string (mock/teste)
        if isinstance(name, str) and name.strip().startswith('{') and name.strip().endswith('}'):
            try:
                data = json.loads(name)
                name = data.get('name', name)
                uf = data.get('uf', uf)
            except Exception:
                pass
        # Se uf ainda for None, tenta extrair do name se possível
        if not uf and isinstance(name, str):
            import re
            uf_match = re.search(r'uf[\s:]+([A-Z]{2})', name, re.IGNORECASE)
            if uf_match:
                uf = uf_match.group(1)
        try: # prepara a requisicao paraa a API
            payload = {
                "name": name,
                "uf": uf
            }

            response = requests.post( #faz a req p/ API
                f"{self.api_base_url}/fetch_oab",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120 # Temp para a req
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("error"): # Se houver erro
                    return f"Erro na busca: {data['error']}"
                
                result = {
                    "oab": data.get("oab", "N/A"),
                    "name": data.get("name", "N/A"),
                    "uf": data.get("uf", "N/A"),
                    "categoria": data.get("categoria", "N/A"),
                    "data_inscricao": data.get("data_inscricao", "N/A"),
                    "situacao": data.get("situacao", "N/A")
                }
                return json.dumps(result, ensure_ascii=False)
            else:
                return f"Erro na API: {response.status_code} - {response.text}"
            
        except requests.exceptions.RequestException as e:
            return f"Erro na conecao da API: {str(e)}"
        except Exception as e:
            return f"Erro inesperado: {str(e)}"
        
    async def _arun(self, name: str, uf: str) -> str:
        return self._run(name, uf)

    def run(self, *args, **kwargs):
        # Se vier apenas um argumento positional, pode ser o JSON
        if args and isinstance(args[0], str) and args[0].strip().startswith('{'):
            try:
                data = json.loads(args[0])
                name = data.get('name')
                uf = data.get('uf')
                return self._run(name, uf)
            except Exception:
                pass
        # Se vier como kwargs normais
        name = kwargs.get('name')
        uf = kwargs.get('uf')
        return self._run(name, uf)