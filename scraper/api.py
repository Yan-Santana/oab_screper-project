from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
from oab_scraper import scrape_oab_async

#Config do logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OAB Scraper API",
    description="API para buscar informações de advogados no site da  OAB",
    version="1.0.0"
)

#Configuração do CORS - Acesso a API de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OABRequest(BaseModel): # Modelo para requisicao de colsulta OAB
    name: str = Field(..., description="Nome Completo do advogado", min_length=1)
    uf: str = Field(..., description="UF/Seccional do advogado", min_length=2, max_length=2)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "FULANO DE TAL",
                "uf": "SP"
            }
        }

class OABResponse(BaseModel): # Modelo para resposta da consulta OAB
    oab: Optional[str] = Field(None, description="Numero de inscricao do advogado(AOB)")
    name: Optional[str] = Field(None, description="Nome completo do advogado")
    uf: Optional[str] = Field(None, description="UF/Seccional do advogado")
    categoria: Optional[str] = Field(None, description="Categoria do advogado")
    data_inscricao: Optional[str] = Field(None, description="Data de inscricao do advogado")
    situacao: Optional[str] = Field(None, description="Situacao do advogado")
    error: Optional[str] = Field(None, description="Mensagem de erro se a consulta falhar")
        
    class Config:
        json_schema_extra = {
            "example": {
                "oab": "123456",
                "name": "FULANO DE TAL",
                "uf": "SP",
                "categoria": "Advogado",
                "data_inscricao": "01/01/2000",
                "situacao": "Ativo"
            }
        }

class ErrorResponse(BaseModel): # Modelo para resposta de erro
    error: str = Field(..., description="Mensagem de erro")
    detail: Optional[str] = Field(None, description="Detalhes do erro")
    
@app.get("/") # Endpoint raiz da API
async def root():
    return {
        "message": "OAB Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "fetch_oab": "POST /fetch_oab - Consulta dados do advogado",
            "health": "GET /health - Verifica o status da API"
        }
    }
    
@app.get("/health") # Endpoint de status da API
async def health_check():
    return {
        "status": "ok!", 
        "message": "API esta online!!"
        }
    
@app.post("/fetch_oab", response_model=OABResponse)
async def fetch_oab(request: OABRequest):
    '''
    Consulta dados do advogado na OAB
    
    Args:
        request: Dados da req contendo o nome e UF
        
    Returns:
        OABResponse: Dados do advogado ou se ocorrer erro
        
    Raises:
        HttpException: Se caso de erro na validacao ou processamento
    '''
    try:
        logger.info(f"🔎 Iniciando Consulta para: {request.name} - {request.uf}")
        
        valid_ufs = [
            "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", 
            "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", 
            "RO", "RR", "RS", "SC", "SE", "SP", "TO"]
        
        # Validação extra para nome e UF
        if not request.name or not request.name.strip():
            raise HTTPException(
                status_code=400,
                detail="O nome do advogado é obrigatório e não pode ser vazio."
            )
        if not request.uf or not request.uf.strip():
            raise HTTPException(
                status_code=400,
                detail="A UF é obrigatória e não pode ser vazia."
            )
        if request.uf.upper() not in valid_ufs:
            raise HTTPException(
                status_code=400,
                detail=f"UF invalida: {request.uf}. UFs validas: {', '.join(valid_ufs)}"
            )
        
        # Executa o scraper de forma assíncrona
        result = await scrape_oab_async(request.name.strip(), request.uf.upper())
        
        logger.info(f"🔎 Consulta finalizada para: {result}")
        
        # Verifica se ocorreu erro
        if "error" in result:
            logger.warning(f"🔴 Erro na consulta: {result['error']}")
            return OABResponse(error=result["error"])
        # Mapeia os campos do resultado para os nomes esperados pelo OABResponse
        result["oab"] = result.get("inscricao")
        result["name"] = result.get("nome")
        # Retorna os dados encontrados
        return OABResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no servidor: {str(e)}"
        )

# Handler para erros de validação dos campos obrigatórios
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Erro de validação nos dados enviados.",
            "detail": exc.errors()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
   