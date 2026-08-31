import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
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


@app.get("/")
async def root():
    return FileResponse(os.path.join("static", "index.html"))


@app.get("/inscripcion")
async def inscripcion_page():
    return FileResponse(os.path.join("static", "inscripcion.html"))


app.mount("/static", StaticFiles(directory="static"), name="static")


async def run_ingest():
    from rag.ingest import ingester

    logger.info("Starting document ingestion...")
    stats = await ingester.ingest_documents()
    logger.info(f"Ingestion complete: {stats}")
    return stats


def main():
    import uvicorn

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "ingest":
            stats = asyncio.run(run_ingest())
            print(f"Ingestion complete: {stats}")
            return

        if command == "serve":
            pass
        else:
            print(f"Unknown command: {command}")
            print("Usage: python main.py [serve|ingest]")
            sys.exit(1)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
