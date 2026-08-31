import os
import re
import hashlib
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from google import genai
from config.settings import settings
from rag.chunker import chunker


class Ingester:
    def __init__(self):
        self._client = None
        self.collection = settings.qdrant_collection_name
        self.genai_client = genai.Client(api_key=settings.gemini_api_key)
        self.embedding_model = settings.gemini_embedding_model

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(path=settings.qdrant_path)
        return self._client

    def _ensure_collection(self) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=3072,
                    distance=Distance.COSINE,
                ),
            )

    def _compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _document_exists(self, document_name: str) -> bool:
        try:
            result = self.client.count(
                collection_name=self.collection,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_name",
                            match=MatchValue(value=document_name),
                        )
                    ]
                ),
            )
            return result.count > 0
        except Exception:
            return False

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            result = self.genai_client.models.embed_content(
                model=self.embedding_model,
                contents=text,
            )
            embeddings.append(result.embeddings[0].values)
        return embeddings

    def _split_sections(self, content: str, filename: str) -> list[dict]:
        sections = []
        current_section = ""
        current_title = "General"

        for line in content.split("\n"):
            if line.startswith("## ") or line.startswith("### "):
                if current_section.strip():
                    sections.append({
                        "title": current_title,
                        "content": current_section.strip(),
                        "filename": filename,
                    })
                current_title = line.lstrip("#").strip()
                current_section = ""
            else:
                current_section += line + "\n"

        if current_section.strip():
            sections.append({
                "title": current_title,
                "content": current_section.strip(),
                "filename": filename,
            })

        return sections

    async def ingest_documents(self, documents_dir: str = None) -> dict:
        documents_dir = documents_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "documents"
        )

        self._ensure_collection()
        stats = {"documents_processed": 0, "chunks_created": 0, "skipped": 0}

        md_files = list(Path(documents_dir).glob("*.md"))

        for md_file in md_files:
            document_name = md_file.stem
            document_path = str(md_file)

            if self._document_exists(document_name):
                stats["skipped"] += 1
                continue

            content = md_file.read_text(encoding="utf-8")
            sections = self._split_sections(content, md_file.name)

            all_chunks = []
            for section in sections:
                chunks = chunker.chunk_with_metadata(
                    text=section["content"],
                    document_name=document_name,
                    document_path=document_path,
                    section=section["title"],
                )
                all_chunks.extend(chunks)

            if not all_chunks:
                continue

            texts = [c["text"] for c in all_chunks]
            embeddings = self._get_embeddings(texts)

            points = []
            for i, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
                chunk_hash = self._compute_hash(chunk["text"])
                point_id = abs(hash(f"{document_name}_{chunk_hash}_{i}")) % (2**63)
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk["text"],
                            "chunk_id": chunk["chunk_id"],
                            "document_name": chunk["document_name"],
                            "document_path": chunk["document_path"],
                            "section": chunk["section"],
                            "source": chunk["source"],
                        },
                    )
                )

            self.client.upsert(
                collection_name=self.collection,
                points=points,
            )

            stats["documents_processed"] += 1
            stats["chunks_created"] += len(points)

        return stats


ingester = Ingester()
