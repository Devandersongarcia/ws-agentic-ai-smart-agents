"""Quality assurance and tracing module for RAG pipeline with Langfuse integration and document validation"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path
from llama_index.core import VectorStoreIndex
from llama_index.core.callbacks import CallbackManager
from llama_index.callbacks.langfuse import langfuse_callback_handler
from llama_index.core import Document
import config

class QualityAssurance:
    
    def __init__(self, index: Optional[VectorStoreIndex] = None):
        """Initialize QA module with optional vector store index."""
        self.index = index
        self.eval_results = []
        
    def evaluate_retrieval_quality(
        self,
        test_queries: List[str],
        expected_contexts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Test retrieval quality using predefined queries."""
        if not self.index:
            raise ValueError("Index not set for evaluation")
            
        query_engine = self.index.as_query_engine()
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(test_queries),
            "evaluations": []
        }
        
        for i, query in enumerate(test_queries):
            response = query_engine.query(query)
            
            eval_item = {
                "query": query,
                "response": str(response),
                "source_nodes": len(response.source_nodes),
                "metadata": []
            }
            
            for node in response.source_nodes:
                eval_item["metadata"].append({
                    "score": node.score,
                    "restaurant": node.metadata.get("restaurant", "unknown"),
                    "section": node.metadata.get("section", "unknown"),
                    "cuisine": node.metadata.get("cuisine", "unknown")
                })
                
            if expected_contexts and i < len(expected_contexts):
                eval_item["expected_context"] = expected_contexts[i]
                eval_item["context_match"] = expected_contexts[i].lower() in str(response).lower()
                
            results["evaluations"].append(eval_item)
            
        results["success_rate"] = sum(
            1 for e in results["evaluations"] 
            if e.get("context_match", True)
        ) / len(test_queries)
        
        self.eval_results.append(results)
        return results
    
    def validate_metadata_completeness(
        self,
        documents: List[Document]
    ) -> Dict[str, Any]:
        """Check metadata field coverage across document batch."""
        report = {
            "total_documents": len(documents),
            "metadata_coverage": {},
            "missing_critical": [],
            "quality_score": 0
        }
        
        critical_fields = ["restaurant", "cuisine", "section", "price_category"]
        optional_fields = ["dietary_options", "dishes", "search_tags"]
        
        for field in critical_fields + optional_fields:
            count = sum(1 for doc in documents if field in doc.metadata)
            coverage = count / len(documents) * 100
            report["metadata_coverage"][field] = {
                "count": count,
                "percentage": round(coverage, 2)
            }
            
            if field in critical_fields and coverage < 80:
                report["missing_critical"].append(field)
                
        critical_coverage = sum(
            report["metadata_coverage"][field]["percentage"]
            for field in critical_fields
        ) / len(critical_fields)
        
        report["quality_score"] = round(critical_coverage, 2)
        
        return report
    
    def check_chunk_quality(
        self,
        chunks: List[Document]
    ) -> Dict[str, Any]:
        """Analyze chunk size distribution and quality metrics."""
        report = {
            "total_chunks": len(chunks),
            "avg_chunk_size": 0,
            "min_chunk_size": 0,
            "max_chunk_size": 0,
            "empty_chunks": 0,
            "quality_issues": []
        }
        
        if not chunks:
            return report
            
        chunk_sizes = [len(chunk.text) for chunk in chunks]
        
        report["avg_chunk_size"] = sum(chunk_sizes) / len(chunk_sizes)
        report["min_chunk_size"] = min(chunk_sizes)
        report["max_chunk_size"] = max(chunk_sizes)
        report["empty_chunks"] = sum(1 for size in chunk_sizes if size < 10)
        
        if report["empty_chunks"] > 0:
            report["quality_issues"].append(f"{report['empty_chunks']} empty chunks found")
            
        if report["max_chunk_size"] > 2000:
            report["quality_issues"].append("Some chunks exceed 2000 characters")
            
        if report["avg_chunk_size"] < 100:
            report["quality_issues"].append("Average chunk size too small")
            
        return report
    
    def generate_test_queries(
        self,
        documents: List[Document],
        num_queries: int = 10
    ) -> List[str]:
        """Generate test queries from document metadata."""
        queries = []
        
        query_templates = [
            "What {cuisine} dishes are available?",
            "Show me vegetarian options at {restaurant}",
            "What are the prices for {section}?",
            "Find {dietary} friendly meals",
            "What's on the menu at {restaurant}?",
            "List all {section} under ${price}",
            "What {cuisine} restaurants offer {dietary} options?",
            "Find dishes with {ingredient}",
            "Show me the specials at {restaurant}",
            "What's the most expensive item in {section}?"
        ]
        
        cuisines = list(set(doc.metadata.get("cuisine", "") for doc in documents if "cuisine" in doc.metadata))
        restaurants = list(set(doc.metadata.get("restaurant", "") for doc in documents if "restaurant" in doc.metadata))
        sections = ["appetizers", "main courses", "desserts", "beverages"]
        dietary = ["vegetarian", "vegan", "gluten-free"]
        
        for i in range(min(num_queries, len(query_templates))):
            template = query_templates[i]
            query = template.format(
                cuisine=cuisines[i % len(cuisines)] if cuisines else "Italian",
                restaurant=restaurants[i % len(restaurants)] if restaurants else "Restaurant",
                section=sections[i % len(sections)],
                dietary=dietary[i % len(dietary)],
                price=20 + (i * 5),
                ingredient="chicken" if i % 2 == 0 else "pasta"
            )
            queries.append(query)
            
        return queries

class PipelineTracer:
    
    def __init__(self, enable_langfuse: bool = False):
        """Initialize pipeline tracer with optional Langfuse integration."""
        self.traces = []
        self.enable_langfuse = enable_langfuse
        self.callback_manager = None
        
        if enable_langfuse and config.LANGFUSE_SECRET_KEY:
            self.setup_langfuse()
            
    def setup_langfuse(self):
        """Configure Langfuse for pipeline observability."""
        try:
            handler = langfuse_callback_handler(
                secret_key=config.LANGFUSE_SECRET_KEY,
                public_key=config.LANGFUSE_PUBLIC_KEY,
                host=config.LANGFUSE_HOST
            )
            self.callback_manager = CallbackManager([handler])
            print("Langfuse tracing enabled")
        except Exception as e:
            print(f"Failed to setup Langfuse: {e}")
            
    def trace_step(
        self,
        step_name: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record execution trace for pipeline step."""
        trace = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "input_summary": self._summarize_data(input_data),
            "output_summary": self._summarize_data(output_data),
            "metadata": metadata or {}
        }
        
        self.traces.append(trace)
        
    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """Create compact summary of data for tracing."""
        if isinstance(data, list):
            return {
                "type": "list",
                "count": len(data),
                "sample": str(data[0])[:100] if data else None
            }
        elif isinstance(data, dict):
            return {
                "type": "dict",
                "keys": list(data.keys()),
                "sample": str(data)[:100]
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)[:100]
            }
            
    def save_traces(self, output_path: Path):
        """Export trace data to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.traces, f, indent=2)
            
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance analysis from trace data."""
        if not self.traces:
            return {"message": "No traces available"}
            
        summary = {
            "total_steps": len(self.traces),
            "steps": {},
            "timeline": []
        }
        
        for trace in self.traces:
            step = trace["step"]
            if step not in summary["steps"]:
                summary["steps"][step] = 0
            summary["steps"][step] += 1
            
            summary["timeline"].append({
                "time": trace["timestamp"],
                "step": step
            })
            
        return summary

def create_qa_suite(index: VectorStoreIndex) -> QualityAssurance:
    """Create quality assurance suite with vector store index."""
    return QualityAssurance(index)

def create_tracer(enable_langfuse: bool = True) -> PipelineTracer:
    """Create pipeline tracer with optional Langfuse observability."""
    return PipelineTracer(enable_langfuse)

def get_callback_manager(tracer: Optional[PipelineTracer] = None) -> Optional[CallbackManager]:
    """Get callback manager from tracer if available."""
    if tracer and tracer.callback_manager:
        return tracer.callback_manager
    return None