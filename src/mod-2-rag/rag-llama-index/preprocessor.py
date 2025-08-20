"""Main RAG preprocessing pipeline orchestrator managing document ingestion, transformation, chunking, and indexing to vector database"""

from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

try:
    from .ingestion import DocumentIngestor
    from .transformer import create_transformation_pipeline
    from .chunking import create_chunking_pipeline
    from .indexer import create_indexer
    from .quality import create_tracer, get_callback_manager
    from . import config
except ImportError:
    from ingestion import DocumentIngestor
    from transformer import create_transformation_pipeline
    from chunking import create_chunking_pipeline
    from indexer import create_indexer
    from quality import create_tracer, get_callback_manager
    import config

class RAGPreprocessor:
    """End-to-end RAG preprocessing pipeline from documents to vector database"""
    
    def __init__(
        self,
        mode: str = "multi",
        storage_dir: Path = config.STORAGE_DIR,
        output_dir: Path = config.OUTPUT_DIR,
        enable_tracing: bool = True
    ):
        """Initialize RAG preprocessor with configuration and tracing."""
        self.mode = mode
        self.storage_dir = Path(storage_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.tracer = create_tracer(enable_tracing) if enable_tracing else None
        self.indexer = None
        self.documents = []
        self.chunks = []
        
    def process(self) -> Dict[str, Any]:
        """Execute complete preprocessing pipeline from ingestion to indexing."""
        """Execute complete preprocessing pipeline"""
        print(f"🚀 Starting RAG Preprocessing Pipeline (Mode: {self.mode.upper()})")
        results = {"mode": self.mode}
        
        print("\n📥 Step 1: Document Ingestion")
        results["ingestion"] = self._run_ingestion()
        
        print("\n🔄 Step 2: Document Transformation")
        results["transformation"] = self._run_transformation()
        
        print("\n✂️ Step 3: Chunking")
        results["chunking"] = self._run_chunking()
        
        print(f"\n💾 Step 4: Vector Database Indexing ({self.mode} collection mode)")
        results["indexing"] = self._run_indexing()
        
        print(f"\n🚀 RAG Preprocessing Complete!")
        self._save_results(results)
        
        return results
    
    def _run_ingestion(self) -> Dict[str, Any]:
        """Load documents from storage directory."""
        ingestor = DocumentIngestor(self.storage_dir)
        
        if self.tracer:
            self.tracer.trace_step("ingestion_start", self.storage_dir, None)
            
        self.documents = ingestor.ingest_all()
        summary = ingestor.get_staging_summary()
        
        if self.tracer:
            self.tracer.trace_step("ingestion_complete", None, summary)
            
        print(f"  ✓ Ingested {len(self.documents)} documents")
        print(f"  ✓ File types: {summary['by_type']}")
        
        return summary
    
    def _run_transformation(self) -> Dict[str, Any]:
        """Apply text cleaning and metadata enrichment."""
        transformation_pipeline = create_transformation_pipeline()
        
        if self.tracer:
            self.tracer.trace_step("transformation_start", len(self.documents), None)
            
        for transformer in transformation_pipeline:
            self.documents = transformer(self.documents)
            
        stats = {
            "processed_documents": len(self.documents),
            "transformations_applied": len(transformation_pipeline)
        }
        
        if self.tracer:
            self.tracer.trace_step("transformation_complete", None, stats)
            
        print(f"  ✓ Transformed {len(self.documents)} documents")
        print(f"  ✓ Applied {len(transformation_pipeline)} transformations")
        
        return stats
    
    def _run_chunking(self) -> Dict[str, Any]:
        """Split documents into semantic chunks."""
        chunker = create_chunking_pipeline(use_semantic=True)
        
        if self.tracer:
            self.tracer.trace_step("chunking_start", len(self.documents), None)
            
        self.chunks = chunker.chunk_documents(self.documents)
        
        stats = {
            "original_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "avg_chunks_per_doc": len(self.chunks) / len(self.documents) if self.documents else 0
        }
        
        if self.tracer:
            self.tracer.trace_step("chunking_complete", None, stats)
            
        print(f"  ✓ Created {len(self.chunks)} chunks")
        print(f"  ✓ Average {stats['avg_chunks_per_doc']:.1f} chunks per document")
        
        return stats
    
    def _run_indexing(self) -> Dict[str, Any]:
        """Index documents to Astra DB vector collections."""
        callback_manager = get_callback_manager(self.tracer) if self.tracer else None
        self.indexer = create_indexer(mode=self.mode, callback_manager=callback_manager)
        
        if self.tracer:
            self.tracer.trace_step("indexing_start", len(self.chunks), None)
            
        print("  ⏳ Categorizing and indexing documents...")
        
        categorized = self.indexer.categorize_documents(self.chunks)
        stats = self.indexer.index_documents(categorized)
        
        if self.tracer:
            self.tracer.trace_step("indexing_complete", None, stats)
            
        if self.mode == "single":
            print(f"  ✓ Indexed {stats['total_documents']} documents in single collection")
        else:
            print(f"  ✓ Indexed {stats['total_documents']} documents across {len(stats['collections'])} collections")
            for collection, info in stats['collections'].items():
                if info.get('status') == 'success':
                    print(f"    • {collection}: {info['document_count']} documents")
                    
        return stats
    
    def _save_results(self, results: Dict[str, Any]):
        """Save processing results and traces to output directory."""
        results["execution_time"] = datetime.now().isoformat()
        results["configuration"] = {
            "mode": self.mode,
            "embedding_model": config.EMBEDDING_MODEL,
            "chunk_size": config.CHUNK_SIZE_TOKENS,
            "storage_dir": str(self.storage_dir),
            "output_dir": str(self.output_dir)
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"preprocessing_results_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        if self.tracer:
            trace_file = self.output_dir / f"preprocessing_traces_{timestamp}.json"
            self.tracer.save_traces(trace_file)
            
        print(f"\n📁 Results saved to: {output_file}")

def create_preprocessor(mode: str = "multi") -> RAGPreprocessor:
    """Create RAG preprocessor with specified collection mode."""
    return RAGPreprocessor(mode=mode)

def main():
    """Command-line entry point for RAG preprocessing pipeline."""
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "multi"
    
    if mode not in ["single", "multi"]:
        print("Usage: python preprocessor.py [single|multi]")
        sys.exit(1)
    
    preprocessor = create_preprocessor(mode=mode)
    results = preprocessor.process()
    
    print(f"\n🎉 {mode.title()}-collection preprocessing completed successfully!")
    print(f"Final Statistics:")
    print(f"  • Documents processed: {results['ingestion']['total_documents']}")
    print(f"  • Chunks created: {results['chunking']['total_chunks']}")
    
    if "indexing" in results:
        if mode == "single":
            print(f"  • Documents indexed: {results['indexing']['total_documents']}")
        else:
            print(f"  • Collections created: {len(results['indexing']['collections'])}")
            print(f"  • Total documents indexed: {results['indexing']['total_documents']}")

if __name__ == "__main__":
    main()