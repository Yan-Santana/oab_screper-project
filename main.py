"""
OAB Scraper + LLM Agent - Script Principal

Este script permite executar o sistema completo ou componentes individuais.
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

# Adicionar diretórios ao path
sys.path.append(str(Path(__file__).parent / "scraper"))
sys.path.append(str(Path(__file__).parent / "agent"))

def main():
    parser = argparse.ArgumentParser(
        description="OAB Scraper + LLM Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py api                    # Executar apenas a API
  python main.py agent                  # Executar apenas o agente
  python main.py test                   # Testar o scraper
  python main.py query "João Silva SP"  # Consulta rápida
        """
    )
    
    parser.add_argument(
        "command",
        choices=["api", "agent", "test", "query"],
        help="Comando a executar"
    )
    
    parser.add_argument(
        "query_text",
        nargs="?",
        help="Texto da consulta (para comando 'query')"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta para a API (padrão: 8000)"
    )
    
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "ollama", "cloudflare", "cloudflare_openai", "mock"],
        default="mock",
        help="Provedor do LLM (padrão: mock)"
    )
    
    args = parser.parse_args()
    
    if args.command == "api":
        run_api(args.port)
    elif args.command == "agent":
        run_agent(args.llm_provider)
    elif args.command == "test":
        run_test()
    elif args.command == "query":
        if not args.query_text:
            print("Erro: Forneça o texto da consulta")
            sys.exit(1)
        run_query(args.query_text, args.llm_provider)

def run_api(port=8000):
    """Executar servidor da API"""
    print(f"🚀 Iniciando servidor da API na porta {port}...")
    
    try:
        import uvicorn
        from scraper.api import app
        
        uvicorn.run(
            "scraper.api:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("Erro: FastAPI/Uvicorn não encontrado. Instale as dependências.")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao iniciar API: {e}")
        sys.exit(1)

def run_agent(llm_provider="mock"):
    """Executar agente LLM interativo"""
    print(f"🤖 Iniciando agente LLM (provedor: {llm_provider})...")
    
    try:
        from agent.llm_agent import OABAgent
        
        
        agent = OABAgent(llm_provider=llm_provider)
        
        print("\n=== Agente OAB LLM ===")
        print("Digite suas perguntas sobre advogados da OAB")
        print("Digite 'sair' para encerrar\n")
        
        while True:
            try:
                question = input("Pergunta: ").strip()
                
                if question.lower() in ['sair', 'exit', 'quit']:
                    print("Encerrando...")
                    break
                
                if not question:
                    continue
                
                print("\nProcessando...")
                response = agent.query(question)
                print(f"\nResposta: {response}")
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\nEncerrando...")
                break
            except Exception as e:
                print(f"Erro: {str(e)}")
                
    except ImportError as e:
        print(f"Erro: Dependências não encontradas: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao iniciar agente: {e}")
        sys.exit(1)

def run_test():
    """Testar o scraper"""
    print("🧪 Testando scraper...")
    
    try:
        from scraper.oab_scraper import scrape_oab
        
        # Teste com dados fictícios
        print("Testando com dados fictícios...")
        result = scrape_oab("FULANO DE TAL", "SP")
        print(f"Resultado: {result}")
        
        if "error" in result:
            print("✅ Teste passou - erro esperado para dados fictícios")
        else:
            print("⚠️  Resultado inesperado")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        sys.exit(1)

def run_query(query_text, llm_provider="mock"):
    """Executar consulta rápida"""
    print(f"🔍 Executando consulta: {query_text}")
    
    try:
        from agent.llm_agent import OABAgent
        
        agent = OABAgent(llm_provider=llm_provider)
        response = agent.query(query_text)
        
        print(f"\nResposta: {response}")
        
    except Exception as e:
        print(f"Erro na consulta: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()