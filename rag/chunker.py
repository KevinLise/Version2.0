import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TokenChunker:
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._encoder = tiktoken.get_encoding("cl100k_base")
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._token_length,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def _token_length(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def chunk_text(self, text: str) -> list[str]:
        chunks = self._splitter.split_text(text)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def chunk_with_metadata(
        self,
        text: str,
        document_name: str,
        document_path: str,
        section: str = "",
    ) -> list[dict]:
        chunks = self.chunk_text(text)
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "text": chunk,
                "chunk_id": f"{document_name}__chunk_{i}",
                "document_name": document_name,
                "document_path": document_path,
                "section": section,
                "source": document_path,
            })
        return result


chunker = TokenChunker()
