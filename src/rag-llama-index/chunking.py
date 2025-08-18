"""Intelligent chunking module for splitting restaurant menu documents into semantically meaningful chunks with menu-aware logic"""

from typing import List, Optional
from llama_index.core import Document
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
    SentenceSplitter,
    SentenceWindowNodeParser
)
from llama_index.embeddings.openai import OpenAIEmbedding
try:
    from . import config
except ImportError:
    import config

class SmartChunker:
    
    def __init__(
        self,
        chunk_size: int = config.CHUNK_SIZE_TOKENS,
        chunk_overlap: int = config.CHUNK_OVERLAP_TOKENS,
        use_semantic: bool = True
    ):
        """Initialize chunker with size limits and semantic splitting option."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_semantic = use_semantic
        
        if use_semantic:
            self.embed_model = OpenAIEmbedding(
                model=config.EMBEDDING_MODEL,
                api_key=config.OPENAI_API_KEY
            )
            self.splitter = SemanticSplitterNodeParser(
                embed_model=self.embed_model,
                buffer_size=1,
                breakpoint_percentile_threshold=95,
                include_metadata=True,
                include_prev_next_rel=True
            )
        else:
            self.splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks using menu-aware and semantic strategies."""
        nodes = []
        
        for doc in documents:
            if self._is_menu_item_doc(doc):
                chunked = self._chunk_by_menu_items(doc)
            elif self._is_structured_doc(doc):
                chunked = self._chunk_by_sections(doc)
            else:
                chunked = self.splitter.get_nodes_from_documents([doc])
                
            for chunk in chunked:
                chunk.metadata.update(doc.metadata)
                
            nodes.extend(chunked)
            
        return nodes
    
    def _is_menu_item_doc(self, doc: Document) -> bool:
        """Check if document contains menu items with prices."""
        return "menu_items" in doc.metadata or "$" in doc.text
    
    def _is_structured_doc(self, doc: Document) -> bool:
        """Check if document has clear section headers."""
        section_keywords = [
            "APPETIZERS", "MAIN COURSES", "DESSERTS",
            "BEVERAGES", "SIDES", "SOUPS", "SALADS", "SPECIALS"
        ]
        return any(keyword in doc.text for keyword in section_keywords)
    
    def _chunk_by_menu_items(self, doc: Document) -> List[Document]:
        """Create chunks focused on individual menu items or small groups."""
        chunks = []
        text = doc.text
        
        sections = self._split_by_sections(text)
        
        for section_name, section_text in sections:
            items = self._extract_items_from_section(section_text)
            
            if items:
                for i in range(0, len(items), 2):
                    chunk_items = items[i:i+2]
                    chunk_text = "\n".join(chunk_items)
                    
                    chunk = Document(
                        text=chunk_text,
                        metadata={
                            **doc.metadata,
                            "section": section_name,
                            "chunk_type": "menu_items",
                            "item_count": len(chunk_items)
                        }
                    )
                    chunks.append(chunk)
            else:
                chunk = Document(
                    text=section_text[:self.chunk_size * 4],
                    metadata={
                        **doc.metadata,
                        "section": section_name,
                        "chunk_type": "section"
                    }
                )
                chunks.append(chunk)
                
        if not chunks:
            return self.splitter.get_nodes_from_documents([doc])
            
        return chunks
    
    def _chunk_by_sections(self, doc: Document) -> List[Document]:
        """Create chunks based on document section boundaries."""
        chunks = []
        text = doc.text
        
        sections = self._split_by_sections(text)
        
        for section_name, section_text in sections:
            if len(section_text) > self.chunk_size * 4:
                section_chunks = self.splitter.get_nodes_from_documents([
                    Document(text=section_text)
                ])
                for chunk in section_chunks:
                    chunk.metadata.update({
                        **doc.metadata,
                        "section": section_name,
                        "chunk_type": "section_part"
                    })
                    chunks.append(chunk)
            else:
                chunk = Document(
                    text=section_text,
                    metadata={
                        **doc.metadata,
                        "section": section_name,
                        "chunk_type": "section_complete"
                    }
                )
                chunks.append(chunk)
                
        if not chunks:
            return self.splitter.get_nodes_from_documents([doc])
            
        return chunks
    
    def _split_by_sections(self, text: str) -> List[tuple]:
        """Split text into named sections based on menu keywords."""
        section_keywords = [
            "APPETIZERS", "MAIN COURSES", "DESSERTS",
            "BEVERAGES", "SIDES", "SOUPS", "SALADS", "SPECIALS"
        ]
        
        sections = []
        current_section = "GENERAL"
        current_text = []
        
        lines = text.split('\n')
        for line in lines:
            found_section = False
            for keyword in section_keywords:
                if keyword in line.upper():
                    if current_text:
                        sections.append((current_section, '\n'.join(current_text)))
                    current_section = keyword
                    current_text = [line]
                    found_section = True
                    break
                    
            if not found_section:
                current_text.append(line)
                
        if current_text:
            sections.append((current_section, '\n'.join(current_text)))
            
        return sections if sections else [("GENERAL", text)]
    
    def _extract_items_from_section(self, text: str) -> List[str]:
        """Extract individual menu items from section text."""
        items = []
        lines = text.split('\n')
        
        current_item = []
        for line in lines:
            if '$' in line:
                if current_item:
                    items.append(' '.join(current_item) + ' ' + line)
                    current_item = []
                else:
                    items.append(line)
            elif line.strip() and not any(kw in line.upper() for kw in ["APPETIZERS", "MAIN", "DESSERTS"]):
                current_item.append(line)
                
        return items

def create_chunking_pipeline(use_semantic: bool = True) -> SmartChunker:
    """Create configured chunking pipeline with semantic splitting option."""
    return SmartChunker(use_semantic=use_semantic)