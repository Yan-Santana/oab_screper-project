# OAB Scraper

## Instalação

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/Yan-Santana/oab_screper-project.git
   cd oab_screper-project
   ```

2. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Instale o Playwright e os browsers:**

   ```bash
   playwright install
   ```

4. **Instale o Tesseract OCR no sistema:**

   - **MacOS:**
     ```bash
     brew install tesseract
     brew install tesseract-lang # para idiomas adicionais
     ```
   - **Ubuntu/Debian:**
     ```bash
     sudo apt-get install tesseract-ocr tesseract-ocr-por
     ```

5. **Pronto! Agora você pode rodar o scraper:**
   ```bash
   python3 scraper/oab_scraper.py
   ```
