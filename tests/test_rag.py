import pytest
from rag.chunker import TokenChunker


class TestChunker:
    def setup_method(self):
        self.chunker = TokenChunker(chunk_size=400, chunk_overlap=50)

    def test_chunk_text_basic(self):
        text = "This is a test sentence. " * 50
        chunks = self.chunker.chunk_text(text)
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)
        assert all(len(c.strip()) > 0 for c in chunks)

    def test_chunk_with_metadata(self):
        text = "Test content for chunking with metadata."
        chunks = self.chunker.chunk_with_metadata(
            text=text,
            document_name="test_doc",
            document_path="/path/to/test.md",
            section="Test Section",
        )
        assert len(chunks) > 0
        for chunk in chunks:
            assert "text" in chunk
            assert "chunk_id" in chunk
            assert "document_name" in chunk
            assert "document_path" in chunk
            assert "section" in chunk
            assert chunk["document_name"] == "test_doc"
            assert chunk["document_path"] == "/path/to/test.md"
            assert chunk["section"] == "Test Section"

    def test_empty_text(self):
        chunks = self.chunker.chunk_text("")
        assert chunks == []

    def test_chunk_preserves_content(self):
        text = "El curso de inglés B1 cuesta 450.000 COP."
        chunks = self.chunker.chunk_text(text)
        assert any("450.000 COP" in c for c in chunks)

    def test_long_text_multiple_chunks(self):
        text = "Paragraph about topic.\n\n" * 200
        chunks = self.chunker.chunk_text(text)
        assert len(chunks) > 1


class TestRAGDocuments:
    def test_documents_exist(self):
        import os
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documents")
        assert os.path.exists(os.path.join(docs_dir, "precios_y_niveles.md"))
        assert os.path.exists(os.path.join(docs_dir, "horarios_y_modalidades.md"))
        assert os.path.exists(os.path.join(docs_dir, "certificaciones_e_inscripciones.md"))

    def test_documents_not_empty(self):
        import os
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documents")
        for fname in ["precios_y_niveles.md", "horarios_y_modalidades.md", "certificaciones_e_inscripciones.md"]:
            path = os.path.join(docs_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            assert len(content) > 100, f"{fname} is too short"

    def test_documents_chunkable(self):
        import os
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documents")
        chunker = TokenChunker()
        for fname in ["precios_y_niveles.md", "horarios_y_modalidades.md", "certificaciones_e_inscripciones.md"]:
            path = os.path.join(docs_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = chunker.chunk_text(content)
            assert len(chunks) > 0, f"{fname} produced no chunks"
