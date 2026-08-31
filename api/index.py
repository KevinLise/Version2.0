import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from database.sqlite import db

    logger.info("Initializing database tables...")
    await db.init_tables()

    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="Academia AI Assistant",
    description="RAG-powered customer support for a language academy",
    version="1.0.0",
    lifespan=lifespan,
)

from api.routes import router

app.include_router(router)


def read_html(file_path: str) -> str:
    static_dir = Path(__file__).parent.parent / "static"
    return (static_dir / file_path).read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=read_html("index.html"))


@app.get("/inscripcion", response_class=HTMLResponse)
async def inscripcion_page():
    return HTMLResponse(content=read_html("inscripcion.html"))
