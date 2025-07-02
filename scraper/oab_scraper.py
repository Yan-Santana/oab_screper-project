from playwright.async_api import async_playwright
import asyncio
from typing import Dict, Any
import re
import pytesseract
from PIL import Image
import requests
from io import BytesIO


def validar_parametros(name: str, uf: str) -> Dict[str, Any]:
    """
    Valido se os parametros de nome e UF estao preenchidos corretamente.
    Vou retornar um dicionario com erro se a validacaao falhar.
    """
    # Remove espacos em branco e verifica se esta vazio
    name_clean = name.strip() if name else ""
    uf_clean = uf.strip() if uf else ""
    
    erros = []
    
    if not name_clean:
        erros.append("Nome é obrigatório")
    
    if not uf_clean:
        erros.append("UF é obrigatória")
    
    # Validacao adicional: nome deve ter pelo menos 2 palavras (nome completo)
    if name_clean and len(name_clean.split()) < 2:
        erros.append("Nome completo é obrigatório (pelo menos nome e sobrenome)")
    
    if erros:
        return {"error": f"Validacao falhou: {'; '.join(erros)}"}
    
    return {"name": name_clean, "uf": uf_clean}


async def extrair_dados_avancados(page, row) -> Dict[str, Any]:
    """
    Extrai dados avancados do resultado, incluindo data de inscricao e situacao.
    Uso multiplos seletores para a variacoes de layout.
    """
    dados = {}
    
    try:
        # Nome - múltiplos seletores possiveis
        nome_selectors = [
            ".rowName span:nth-child(2)",
            ".rowName span:last-child",
            ".rowName .nome",
            ".nome"
        ]
        
        for selector in nome_selectors:
            nome_elem = await row.query_selector(selector)
            if nome_elem:
                dados["nome"] = (await nome_elem.inner_text()).strip()
                break
        
        # Inscricao - múltiplos seletores
        inscricao_selectors = [
            ".rowInsc span:last-child",
            ".rowInsc .inscricao",
            ".inscricao"
        ]
        
        for selector in inscricao_selectors:
            inscricao_elem = await row.query_selector(selector)
            if inscricao_elem:
                dados["inscricao"] = (await inscricao_elem.inner_text()).strip()
                break
        
        # UF - múltiplos seletores
        uf_selectors = [
            ".rowUf span:last-child",
            ".rowUf .uf",
            ".uf"
        ]
        
        for selector in uf_selectors:
            uf_elem = await row.query_selector(selector)
            if uf_elem:
                dados["uf"] = (await uf_elem.inner_text()).strip()
                break
        
        # Categoria/Tipo - múltiplos seletores
        tipo_selectors = [
            ".rowTipoInsc span:last-child",
            ".rowTipoInsc .tipo",
            ".tipo",
            ".categoria"
        ]
        
        for selector in tipo_selectors:
            tipo_elem = await row.query_selector(selector)
            if tipo_elem:
                dados["categoria"] = (await tipo_elem.inner_text()).strip()
                break
        
        # Data de inscricao - busca por padroes de data
        data_selectors = [
            ".rowData span:last-child",
            ".rowData .data",
            ".data",
            ".dataInscricao"
        ]
        
        for selector in data_selectors:
            data_elem = await row.query_selector(selector)
            if data_elem:
                data_text = (await data_elem.inner_text()).strip()
                # Verifica se contém padrao de data
                if re.search(r'\d{2}/\d{2}/\d{4}', data_text):
                    dados["data_inscricao"] = data_text
                    break
        
        # Situacao atual - busca por status/situacao
        situacao_selectors = [
            ".rowSituacao span:last-child",
            ".rowSituacao .situacao",
            ".situacao",
            ".status",
            ".rowStatus span:last-child"
        ]
        
        for selector in situacao_selectors:
            situacao_elem = await row.query_selector(selector)
            if situacao_elem:
                dados["situacao"] = (await situacao_elem.inner_text()).strip()
                break
        
        # Se nao encontrou situacao especifica, tenta buscar no texto completo da linha
        if "situacao" not in dados:
            row_text = await row.inner_text()
            # Busca por palavras-chave de situacao
            situacao_keywords = ["ATIVO", "INATIVO", "SUSPENSO", "CANCELADO", "REGULAR"]
            for keyword in situacao_keywords:
                if keyword in row_text.upper():
                    dados["situacao"] = keyword
                    break
        
        # Busca alternativa: tenta extrair todos os spans da linha
        if len(dados) < 4:  # Se nao conseguiu extrair pelo menos 4 campos
            all_spans = await row.query_selector_all("span")
            span_texts = []
            for span in all_spans:
                text = (await span.inner_text()).strip()
                if text:
                    span_texts.append(text)
            
            # Tenta identificar campos pelos textos
            for i, text in enumerate(span_texts):
                if re.search(r'\d{2}/\d{2}/\d{4}', text) and "data_inscricao" not in dados:
                    dados["data_inscricao"] = text
                elif re.search(r'^\d+$', text) and "inscricao" not in dados:
                    dados["inscricao"] = text
                elif len(text) == 2 and text.isupper() and "uf" not in dados:
                    dados["uf"] = text
                elif text.upper() in ["ADVOGADO", "ESTAGIÁRIO", "ESTAGIARIO"] and "categoria" not in dados:
                    dados["categoria"] = text
                elif text.upper() in ["ATIVO", "INATIVO", "SUSPENSO", "CANCELADO", "REGULAR"] and "situacao" not in dados:
                    dados["situacao"] = text
                elif len(text.split()) >= 2 and "nome" not in dados:
                    dados["nome"] = text
        
    except Exception as e:
        print(f"Erro ao extrair dados avancados: {e}")
    
    return dados


async def extrair_situacao_modal(page):
    # Espera o modal aparecer
    await page.wait_for_selector("#imgDetail", timeout=10000)
    img_elem = await page.query_selector("#imgDetail")
    img_url = await img_elem.get_attribute("src")
    if img_url.startswith("/"):
        img_url = "https://cna.oab.org.br" + img_url
    img_data = requests.get(img_url).content
    image = Image.open(BytesIO(img_data))
    texto = pytesseract.image_to_string(image, lang="eng")
    for palavra in ["REGULAR", "SUSPENSO", "CANCELADO", "INATIVO"]:
        if palavra in texto.upper():
            return palavra
    return texto.strip()


async def scrape_oab_async(name: str, uf: str) -> Dict[str, Any]:
    """ 
    Extrai informacoes de um advogado a partir do nome e UF. De forma assincrona.
    Retorna um dicionario (Dict[str, Any]) com as informacoes extraidas ou erro.
    """
    # Validacao dos parâmetros
    validacao = validar_parametros(name, uf)
    if "error" in validacao:
        return validacao
    
    name_clean = validacao["name"]
    uf_clean = validacao["uf"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print(f"Inicianndo busca na pagina da OAB para buscar:: {name_clean} - {uf_clean}")
            await page.goto("https://cna.oab.org.br/", timeout=120000)
            await page.wait_for_load_state("domcontentloaded")

            await page.fill("#txtName", name_clean)

            await page.select_option("#cmbSeccional", uf_clean)

            await page.click("#btnFind")

            print("Aguardando resultados...")
            await page.wait_for_timeout(5000)  # Aguarda 5s para carregamento do DOM
            
            # Múltiplas tentativas de encontrar resultados
            row = None
            selectors_tentados = ["#divResult .row", ".resultado .row", ".row", ".result-item"]
            
            for selector in selectors_tentados:
                row = await page.query_selector(selector)
                if row:
                    break
            
            if not row:
                # Tenta buscar por qualquer elemento que contenha o nome
                nome_elements = await page.query_selector_all(f"*:has-text('{name_clean.split()[0]}')")
                if nome_elements:
                    # Verifica se algum dos elementos realmente bate com a UF desejada
                    for el in nome_elements:
                        el_text = await el.inner_text()
                        if uf_clean.upper() in el_text.upper():
                            row = el
                            break
                if not row:
                    return {"error": f"Nenhum resultado encontrado para: {name_clean} - {uf_clean}"}
            # Só executa o restante se encontrou resultado
            # Extrai dados usando método avancado
            data = await extrair_dados_avancados(page, row)
            # Tenta clicar e extrair situacao do modal
            try:
                await row.click()
                situacao_modal = await extrair_situacao_modal(page)
                data["situacao"] = situacao_modal
            except Exception:
                if "situacao" not in data or not data["situacao"]:
                    data["situacao"] = "Nao encontrada"
            # Garante que todos os campos obrigatórios estejam presentes
            campos_obrigatorios = ["nome", "inscricao", "uf", "categoria"]
            for campo in campos_obrigatorios:
                if campo not in data or not data[campo]:
                    data[campo] = "Nao encontrado"
            # Adiciona campos opcionais se nao encontrados
            if "data_inscricao" not in data:
                data["data_inscricao"] = "Nao encontrada"

        except Exception as e:
            print(f"Erro durante a navegacao ou busca: {e}")
            data = {"error": f"Erro durante a navegacao ou busca: {e}"}
        finally:
            await browser.close()
        return data


def scrape_oab(name: str, uf: str) -> Dict[str, Any]:
    """
    Extrai informacoes do advogado a partir do nome e UF. De forma sincrona.
    Retorna um dicionario (Dict[str, Any]) com as informacoes extraidas ou erro.
    """
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            import concurrent.futures

            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                try:
                    return new_loop.run_until_complete(scrape_oab_async(name, uf))
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        else:
            return loop.run_until_complete(scrape_oab_async(name, uf))
    except RuntimeError:
        return asyncio.run(scrape_oab_async(name, uf))


if __name__ == "__main__":
    # Testes com diferentes cenarios de validacao
    consultas = [
        ("Luiz Carlos Benedito Hormung Junior", "BA"),  # Valido
        ("Luiz Carlos Benedito Hormung Junior", "MS"), 
        ("Luiz", "MS"),  # Nome incompleto
        ("", "MS"),  # Nome vazio
        ("Luiz Carlos Benedito Hormung Junior", ""),  # UF vazia
        ("", ""),  # Ambos vazios
        ("   ", "   ")  # Apenas espacos
    ]

    for nome, uf in consultas:
        print("\n" + "=" * 80)
        print(f"🔎 Iniciando busca: '{nome}' - '{uf}'\n")

        resultado = scrape_oab(nome, uf)
        print("")
        print(f"🔎 Consulta finalizada: '{nome}' - '{uf}'")
        if "error" in resultado:
            print(f"❌ {resultado['error']}")
        else:
            print("Resultado:")
            print(f"   Nome           : {resultado['nome']}")
            print(f"   Inscricao      : {resultado['inscricao']}")
            print(f"   UF             : {resultado['uf']}")
            print(f"   Categoria      : {resultado['categoria']}")
            print(f"   Data Inscricao : {resultado['data_inscricao']}")
            print(f"   Situacao       : {resultado['situacao']}")


