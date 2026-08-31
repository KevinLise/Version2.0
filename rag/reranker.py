import re


class Reranker:
    """
    Lightweight reranker that combines vector similarity score with
    keyword overlap signals to rerank retrieved documents.

    Strategy: score = alpha * vector_score + beta * keyword_overlap
    where alpha=0.7, beta=0.3. No external API needed.
    """

    def __init__(self, alpha: float = 0.7, beta: float = 0.3):
        self.alpha = alpha
        self.beta = beta

    def _extract_keywords(self, text: str) -> set[str]:
        words = re.findall(r"\b\w{3,}\b", text.lower())
        stopwords = {
            "como", "para", "que", "con", "una", "por", "los", "las",
            "del", "este", "esta", "más", "pero", "tiene", "puede",
            "cuando", "donde", "cuál", "cuánto", "cuánta", "sobre",
            "desde", "hasta", "cada", "todo", "toda", "todos", "todas",
            "otro", "otra", "otros", "otras", "mismo", "misma",
            "the", "and", "for", "are", "but", "not", "you", "all",
            "can", "had", "her", "was", "one", "our", "out", "has",
            "his", "how", "its", "may", "new", "now", "old", "see",
            "way", "who", "did", "get", "let", "say", "she", "too",
            "use",
        }
        return {w for w in words if w not in stopwords}

    def _keyword_overlap_score(self, query: str, document: str) -> float:
        query_keywords = self._extract_keywords(query)
        doc_keywords = self._extract_keywords(document)

        if not query_keywords:
            return 0.0

        overlap = query_keywords & doc_keywords
        return len(overlap) / len(query_keywords)

    async def rerank(self, query: str, documents: list[dict]) -> list[dict]:
        if not documents:
            return []

        reranked = []
        for doc in documents:
            vector_score = doc.get("score", 0.0)
            keyword_score = self._keyword_overlap_score(query, doc.get("text", ""))
            combined_score = (self.alpha * vector_score) + (self.beta * keyword_score)

            reranked.append({
                **doc,
                "rerank_score": combined_score,
                "vector_score": vector_score,
                "keyword_score": keyword_score,
            })

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked


reranker = Reranker()
