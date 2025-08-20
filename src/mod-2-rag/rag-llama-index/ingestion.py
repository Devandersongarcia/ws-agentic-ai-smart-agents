"""Document ingestion module for loading PDF, JSON, CSV, DOCX, and Markdown files from storage directory with metadata extraction"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json
import pandas as pd
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.readers.file import DocxReader

try:
    from . import config
except ImportError:
    import config

class DocumentIngestor:
    
    def __init__(self, storage_dir: Path = config.STORAGE_DIR):
        """Initialize document ingestor with storage directory."""
        self.storage_dir = Path(storage_dir)
        self.staging_data = []
        
    def ingest_all(self) -> List[Document]:
        """Load and process all supported file types from storage directory."""
        documents = []
        
        pdf_docs = self._ingest_pdfs()
        json_docs = self._ingest_json()
        csv_docs = self._ingest_csv()
        md_docs = self._ingest_markdown()
        docx_docs = self._ingest_docx()
        
        documents.extend(pdf_docs)
        documents.extend(json_docs)
        documents.extend(csv_docs)
        documents.extend(md_docs)
        documents.extend(docx_docs)
        
        for idx, doc in enumerate(documents):
            doc.metadata.update({
                "doc_id": f"doc_{idx:04d}",
                "ingestion_timestamp": datetime.now().isoformat()
            })
            
        return documents
    
    def _ingest_pdfs(self) -> List[Document]:
        """Load PDF files from pdf subdirectory."""
        pdf_dir = self.storage_dir / "pdf"
        if not pdf_dir.exists():
            return []
            
        reader = SimpleDirectoryReader(
            input_dir=str(pdf_dir),
            required_exts=[".pdf"],
            recursive=False
        )
        
        docs = reader.load_data()
        for doc in docs:
            doc.metadata["file_type"] = "pdf"
            doc.metadata["source_dir"] = "pdf"
            self._extract_restaurant_metadata(doc)
            
        return docs
    
    def _ingest_json(self) -> List[Document]:
        """Load JSON files and convert each item to a document."""
        json_dir = self.storage_dir / "json"
        if not json_dir.exists():
            return []
            
        documents = []
        for json_file in json_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            if isinstance(data, list):
                for item in data:
                    doc_text = json.dumps(item, indent=2)
                    if len(doc_text) > 1500:
                        doc_text = doc_text[:1500] + "... [truncated]"
                    doc = Document(
                        text=doc_text,
                        metadata={
                            "file_name": json_file.name,
                            "file_type": "json",
                            "source_dir": "json"
                        }
                    )
                    self._extract_json_metadata(doc, item)
                    documents.append(doc)
            else:
                doc_text = json.dumps(data, indent=2)
                if len(doc_text) > 1500:
                    doc_text = doc_text[:1500] + "... [truncated]"
                doc = Document(
                    text=doc_text,
                    metadata={
                        "file_name": json_file.name,
                        "file_type": "json",
                        "source_dir": "json"
                    }
                )
                self._extract_json_metadata(doc, data)
                documents.append(doc)
                
        return documents
    
    def _ingest_csv(self) -> List[Document]:
        """Load CSV files and convert each row to a document."""
        csv_dir = self.storage_dir / "csv"
        if not csv_dir.exists():
            return []
            
        documents = []
        for csv_file in csv_dir.glob("*.csv"):
            df = pd.read_csv(csv_file)
            
            for _, row in df.iterrows():
                doc_text = row.to_json(indent=2)
                doc = Document(
                    text=doc_text,
                    metadata={
                        "file_name": csv_file.name,
                        "file_type": "csv",
                        "source_dir": "csv"
                    }
                )
                self._extract_csv_metadata(doc, row)
                documents.append(doc)
                
        return documents
    
    def _ingest_markdown(self) -> List[Document]:
        """Load markdown files from any subdirectory."""
        md_files = list(self.storage_dir.rglob("*.md"))
        if not md_files:
            return []
            
        documents = []
        for md_file in md_files:
            reader = SimpleDirectoryReader(
                input_files=[str(md_file)]
            )
            docs = reader.load_data()
            for doc in docs:
                doc.metadata["file_type"] = "markdown"
                doc.metadata["source_dir"] = str(md_file.parent.relative_to(self.storage_dir))
                documents.append(doc)
                
        return documents
    
    def _ingest_docx(self) -> List[Document]:
        """Load DOCX files from doc subdirectory."""
        doc_dir = self.storage_dir / "doc"
        if not doc_dir.exists():
            return []
            
        documents = []
        docx_reader = DocxReader()
        
        for docx_file in doc_dir.glob("*.docx"):
            docs = docx_reader.load_data(file=docx_file)
            for doc in docs:
                doc.metadata["file_type"] = "docx"
                doc.metadata["source_dir"] = "doc"
                documents.append(doc)
                
        return documents
    
    def _extract_restaurant_metadata(self, doc: Document):
        """Extract restaurant name from PDF filename."""
        if "file_name" in doc.metadata:
            filename = Path(doc.metadata["file_name"]).stem
            doc.metadata["restaurant"] = filename.replace("_", " ").title()
            doc.metadata["cuisine"] = filename.replace("_", " ").title()
    
    def _extract_json_metadata(self, doc: Document, data: Dict[str, Any]):
        """Extract structured metadata from JSON data."""
        if "restaurant" in data:
            doc.metadata["restaurant"] = data["restaurant"]
        if "cuisine" in data:
            doc.metadata["cuisine"] = data["cuisine"]
        if "dish" in data:
            doc.metadata["dish_name"] = data["dish"]
        if "price" in data:
            doc.metadata["price"] = data["price"]
            
    def _extract_csv_metadata(self, doc: Document, row: pd.Series):
        """Extract metadata from CSV row data."""
        for col in ["restaurant", "cuisine", "dish", "price", "discount", "valid_until"]:
            if col in row and pd.notna(row[col]):
                doc.metadata[col] = row[col]
    
    def get_staging_summary(self) -> Dict[str, Any]:
        """Generate summary statistics of ingested documents."""
        docs = self.ingest_all()
        summary = {
            "total_documents": len(docs),
            "by_type": {},
            "by_source_dir": {}
        }
        
        for doc in docs:
            file_type = doc.metadata.get("file_type", "unknown")
            source_dir = doc.metadata.get("source_dir", "unknown")
            
            summary["by_type"][file_type] = summary["by_type"].get(file_type, 0) + 1
            summary["by_source_dir"][source_dir] = summary["by_source_dir"].get(source_dir, 0) + 1
            
        return summary