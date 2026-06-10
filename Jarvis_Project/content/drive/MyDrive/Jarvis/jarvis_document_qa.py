# jarvis_document_qa.py - Interactive Document Q&A with RAG
# Enables users to upload PDFs/DOCX files and ask questions specifically about their content

import os
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import logging

# Document parsing libraries
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pdfplumber = None
    PDFPLUMBER_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    docx = None
    DOCX_AVAILABLE = False

try:
    import sentence_transformers
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    sentence_transformers = None
    EMBEDDINGS_AVAILABLE = False


class DocumentQAHandler:
    """
    Handles interactive Q&A for uploaded documents using RAG (Retrieval-Augmented Generation).
    Extracts text, chunks it, and provides context-aware answers about document content.
    """
    
    def __init__(self):
        self.documents = {}  # {doc_id: {"path": str, "text": str, "chunks": [str], "embeddings": np.ndarray}}
        self.embeddings_model = None
        self.chunk_size = 500
        self.chunk_overlap = 100
        self.embedding_model_name = os.environ.get("JARVIS_EMBEDDING_MODEL", "all-mpnet-base-v2")
        self._silence_hf_hub_warnings()

    def _silence_hf_hub_warnings(self):
        """Reduce Hugging Face Hub and transformer logging noise for public model downloads."""
        try:
            logging.getLogger("huggingface_hub.utils._http").setLevel(logging.ERROR)
            logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
            logging.getLogger("transformers").setLevel(logging.ERROR)
        except Exception:
            pass

    def _load_embeddings_model(self):
        """Lazily load the SentenceTransformer embeddings model when needed."""
        if self.embeddings_model is not None or not EMBEDDINGS_AVAILABLE:
            return

        try:
            from sentence_transformers import SentenceTransformer
            kwargs = {}
            hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")
            if hf_token:
                kwargs["use_auth_token"] = hf_token
            self.embeddings_model = SentenceTransformer(self.embedding_model_name, **kwargs)
        except Exception as e:
            logging.warning(f"Could not load embeddings model '{self.embedding_model_name}': {e}")
            self.embeddings_model = None
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using pdfplumber."""
        if not PDFPLUMBER_AVAILABLE:
            return "Error: pdfplumber not installed. Install with: pip install pdfplumber"
        
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    text += "\n---PAGE BREAK---\n"
            return text.strip()
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file using python-docx."""
        if not DOCX_AVAILABLE:
            return "Error: python-docx not installed. Install with: pip install python-docx"
        
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            return f"Error extracting DOCX text: {str(e)}"
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error extracting TXT text: {str(e)}"
    
    def extract_document_text(self, file_path: str) -> str:
        """
        Intelligently extract text from various document formats.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            return self.extract_text_from_docx(file_path)
        elif file_ext == ".txt":
            return self.extract_text_from_txt(file_path)
        else:
            return f"Unsupported file format: {file_ext}"
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Split document text into overlapping chunks for context windows.
        
        Args:
            text: Full document text
            chunk_size: Size of each chunk (default: 500)
            overlap: Overlap between chunks (default: 100)
            
        Returns:
            List of text chunks
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap is None:
            overlap = self.chunk_overlap
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def add_document(self, file_path: str, doc_id: str = None) -> Dict[str, any]:
        """
        Add a new document for Q&A.
        
        Args:
            file_path: Path to document
            doc_id: Unique identifier (default: filename)
            
        Returns:
            Status dict with document info
        """
        if doc_id is None:
            doc_id = Path(file_path).stem
        
        # Avoid duplicate IDs
        counter = 1
        original_id = doc_id
        while doc_id in self.documents:
            doc_id = f"{original_id}_{counter}"
            counter += 1
        
        # Extract text
        text = self.extract_document_text(file_path)
        
        if text.startswith("Error"):
            return {"success": False, "error": text, "doc_id": None}
        
        # Chunk text
        chunks = self.chunk_text(text)
        
        # Pre-calculate embeddings if model is available
        embeddings = None
        if chunks:
            self._load_embeddings_model()
            if self.embeddings_model:
                try:
                    embeddings = self.embeddings_model.encode(chunks, convert_to_numpy=True)
                except Exception as e:
                    logging.warning(f"Could not generate embeddings for {doc_id}: {e}")
        
        # Store document
        self.documents[doc_id] = {
            "path": file_path,
            "text": text,
            "chunks": chunks,
            "num_chunks": len(chunks),
            "embeddings": embeddings
        }
        
        return {
            "success": True,
            "doc_id": doc_id,
            "filename": Path(file_path).name,
            "num_chunks": len(chunks),
            "text_length": len(text)
        }
    
    def retrieve_relevant_chunks(self, query: str, doc_id: str, top_k: int = 3) -> List[str]:
        """
        Retrieve the most relevant chunks for a given query.
        Falls back to keyword matching if embeddings unavailable.
        
        Args:
            query: User question
            doc_id: Document to search in
            top_k: Number of chunks to return
            
        Returns:
            List of relevant text chunks
        """
        if doc_id not in self.documents:
            return []
        
        doc = self.documents[doc_id]
        chunks = doc["chunks"]
        chunk_embeddings = doc.get("embeddings")

        # If embeddings available, use semantic search
        if chunk_embeddings is not None and len(chunk_embeddings) > 0:
            self._load_embeddings_model()
            if self.embeddings_model is not None:
                try:
                    query_embedding = self.embeddings_model.encode(query, convert_to_numpy=True)
                    import numpy as np
                    similarities = np.dot(chunk_embeddings, query_embedding)
                    top_indices = np.argsort(similarities, axis=0).flatten()[-top_k:][::-1]
                    return [chunks[i] for i in top_indices if i < len(chunks)]
                except Exception:
                    pass  # Fall through to keyword matching
        
        # Fallback: keyword matching
        query_words = set(query.lower().split())
        chunk_scores = []
        
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            score = len(query_words & chunk_words)  # Intersection count
            chunk_scores.append((chunk, score))
        
        # Return top_k chunks by score
        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in chunk_scores[:top_k]]
    
    def get_document_summary(self, doc_id: str, max_length: int = 300) -> str:
        """
        Get a brief summary of the document (first max_length chars).
        
        Args:
            doc_id: Document identifier
            max_length: Maximum length of summary
            
        Returns:
            Document summary
        """
        if doc_id not in self.documents:
            return "Document not found"
        
        text = self.documents[doc_id]["text"]
        return text[:max_length] + ("..." if len(text) > max_length else "")
    
    def list_documents(self) -> List[Dict[str, any]]:
        """Get list of all loaded documents."""
        return [
            {
                "id": doc_id,
                "filename": Path(self.documents[doc_id]["path"]).name,
                "chunks": self.documents[doc_id]["num_chunks"],
                "size": len(self.documents[doc_id]["text"])
            }
            for doc_id in self.documents
        ]
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the Q&A system."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False
    
    def format_rag_prompt(self, query: str, doc_id: str, relevant_chunks: List[str]) -> str:
        """
        Format a RAG prompt combining query and relevant document context.
        
        Args:
            query: User question
            doc_id: Document being queried
            relevant_chunks: Relevant text chunks from document
            
        Returns:
            Formatted prompt for LLM
        """
        doc_info = self.documents.get(doc_id, {})
        filename = Path(doc_info.get("path", "")).name if "path" in doc_info else doc_id
        
        context = "\n\n".join(relevant_chunks)
        
        prompt = f"""You are an expert document analyst. Answer the following question using ONLY the provided document context.

Document: {filename}

CONTEXT FROM DOCUMENT:
{context}

QUESTION: {query}

Please provide a clear, concise answer based solely on the document context. If the answer cannot be found in the document, say "The document does not contain information about this topic." """
        
        return prompt


# Example usage
if __name__ == "__main__":
    handler = DocumentQAHandler()
    
    # Simulate adding a document
    logging.info("DocumentQAHandler initialized and ready to use")
    logging.info(f"Embeddings available: {handler.embeddings_model is not None}")
