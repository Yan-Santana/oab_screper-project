"""
Testes para a API do scraper OAB
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Adicionar path do projeto
sys.path.append(str(Path(_file_).parent.parent / "scraper"))

from api import app

client = TestClient(app)

def test_root_endpoint():
    """Testar endpoint raiz"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "OAB Scraper API" in data["message"]

def test_health_endpoint():
    """Testar endpoint de saúde"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_fetch_oab_validation():
    """Testar validação do endpoint fetch_oab"""
    # Teste com dados inválidos
    response = client.post("/fetch_oab", json={})
    assert response.status_code == 422  # Validation error
    
    # Teste com UF inválida
    response = client.post("/fetch_oab", json={
        "name": "Teste",
        "uf": "XX"
    })
    assert response.status_code == 400
    
def test_fetch_oab_valid_request():
    """Testar requisição válida (pode retornar erro de scraping)"""
    response = client.post("/fetch_oab", json={
        "name": "FULANO DE TAL",
        "uf": "SP"
    })
    
    # Deve retornar 200 mesmo se não encontrar dados
    assert response.status_code == 200
    data = response.json()
    
    # Deve ter pelo menos um campo de resposta
    assert any(key in data for key in ["oab", "nome", "error"])

def test_openapi_docs():
    """Testar documentação OpenAPI"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data