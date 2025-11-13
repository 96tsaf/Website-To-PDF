import asyncio
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=3)

# Constants
PDF_FORMAT = "A4"
TIMEOUT_MS = 30000
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

app = FastAPI(title="Website to PDF API", version="1.0.0")

static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


class ConvertRequest(BaseModel):
    url: HttpUrl
    format: str = PDF_FORMAT
    landscape: bool = False
    print_background: bool = True


def convert_website_to_pdf_sync(
    url: str,
    format: str = PDF_FORMAT,
    landscape: bool = False,
    print_background: bool = True
) -> bytes:
    """
    Convert a website to PDF using Selenium.
    
    Args:
        url: Website URL to convert
        format: Paper format (A4, Letter, etc)
        landscape: Whether to use landscape orientation
        print_background: Whether to print background graphics
        
    Returns:
        PDF file as bytes
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        logger.info(f"Converting URL to PDF: {url}")
        driver.get(url)
        
        # Configure print settings
        print_options = {
            'landscape': landscape,
            'displayHeaderFooter': False,
            'printBackground': print_background,
            'preferCSSPageSize': True,
            'paperWidth': 8.27 if format == "A4" else 8.5,
            'paperHeight': 11.69 if format == "A4" else 11,
            'marginTop': 0.4,
            'marginBottom': 0.4,
            'marginLeft': 0.4,
            'marginRight': 0.4,
        }
        
        result = driver.execute_cdp_cmd("Page.printToPDF", print_options)
        pdf_bytes = base64.b64decode(result['data'])
        
        logger.info(f"Successfully converted {url}")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error converting {url}: {str(e)}")
        raise
        
    finally:
        driver.quit()


@app.get("/")
async def root():
    """Root endpoint - redirect to test page"""
    return {
        "message": "Website to PDF API",
        "docs": "/docs",
        "test_page": "/static/index.html"
    }


@app.post("/convert")
async def convert_to_pdf(request: ConvertRequest):
    """
    Convert a website to PDF.
    
    Returns a PDF file as a download.
    """
    try:
        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(
            executor,
            convert_website_to_pdf_sync,
            str(request.url),
            request.format,
            request.landscape,
            request.print_background
        )
        
        pdf_buffer = BytesIO(pdf_bytes)
        filename = "website.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

