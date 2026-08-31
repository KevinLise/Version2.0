from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, QueryRequest
from config.settings import settings


class Retriever:
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

    def _get_query_embedding(self, query: str) -> list[float]:
        result = self.genai_client.models.embed_content(
            model=self.embedding_model,
            contents=query,
        )
        return result.embeddings[0].values

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        top_k = top_k or settings.top_k
        query_embedding = self._get_query_embedding(query)

        results = self.client.query_points(
            collection_name=self.collection,
            query=query_embedding,
            limit=top_k,
        )

        documents = []
        for result in results.points:
            payload = result.payload
            documents.append({
                "text": payload.get("text", ""),
                "score": result.score,
                "chunk_id": payload.get("chunk_id", ""),
                "document_name": payload.get("document_name", ""),
                "section": payload.get("section", ""),
                "source": payload.get("source", ""),
            })

        return documents

    async def retrieve_with_filter(
        self,
        query: str,
        document_name: str,
        top_k: int | None = None,
    ) -> list[dict]:
        top_k = top_k or settings.top_k
        query_embedding = self._get_query_embedding(query)

        search_filter = Filter(
            must=[
                FieldCondition(
                    key="document_name",
                    match=MatchValue(value=document_name),
                )
            ]
        )

        results = self.client.query_points(
            collection_name=self.collection,
            query=query_embedding,
            limit=top_k,
            query_filter=search_filter,
        )

        documents = []
        for result in results.points:
            payload = result.payload
            documents.append({
                "text": payload.get("text", ""),
                "score": result.score,
                "chunk_id": payload.get("chunk_id", ""),
                "document_name": payload.get("document_name", ""),
                "section": payload.get("section", ""),
                "source": payload.get("source", ""),
            })

        return documents


retriever = Retriever()
