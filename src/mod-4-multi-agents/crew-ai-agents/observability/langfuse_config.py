"""
Langfuse configuration and integration for CrewAI observability.
Provides comprehensive tracing of agent interactions and LLM calls.
"""

import functools
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe

from config import get_settings


class LangfuseObserver:
    """
    Manages Langfuse observability for multi-agent system.
    Tracks agent interactions, tool usage, and performance metrics.
    """

    def __init__(self):
        """Initialize Langfuse client with configuration."""
        self.settings = get_settings()
        
        self.langfuse = Langfuse(
            public_key=self.settings.langfuse_public_key,
            secret_key=self.settings.langfuse_secret_key,
            host=self.settings.langfuse_host,
            release=self.settings.langfuse_release,
            debug=self.settings.langfuse_debug
        )
        
        self.active_traces = {}
        self.metrics = {
            "total_traces": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "agent_calls": {},
            "tool_calls": {}
        }

    def create_trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Any:
        """
        Create a new trace for tracking an execution flow.
        
        Args:
            name: Name of the trace
            metadata: Optional metadata to attach
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            Trace object
        """
        trace = self.langfuse.trace(
            name=name,
            metadata=metadata or {},
            user_id=user_id,
            session_id=session_id,
            release=self.settings.langfuse_release
        )
        
        trace_id = trace.id
        self.active_traces[trace_id] = trace
        self.metrics["total_traces"] += 1
        
        return trace

    def create_span(
        self,
        trace_id: str,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create a span within a trace.
        
        Args:
            trace_id: Parent trace ID
            name: Name of the span
            input_data: Input data for the span
            metadata: Optional metadata
            
        Returns:
            Span object
        """
        trace = self.active_traces.get(trace_id)
        if not trace:
            raise ValueError(f"No active trace with ID: {trace_id}")
        
        span = trace.span(
            name=name,
            input=input_data,
            metadata=metadata or {}
        )
        
        return span

    def track_agent_execution(
        self,
        agent_name: str,
        task_description: str,
        execution_time: float,
        tokens_used: int,
        cost: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Track an agent execution.
        
        Args:
            agent_name: Name of the agent
            task_description: Description of the task
            execution_time: Time taken in seconds
            tokens_used: Number of tokens consumed
            cost: Estimated cost in dollars
            success: Whether execution was successful
            error: Error message if failed
        """
        self.metrics["total_tokens"] += tokens_used
        self.metrics["total_cost"] += cost
        
        if agent_name not in self.metrics["agent_calls"]:
            self.metrics["agent_calls"][agent_name] = {
                "count": 0,
                "total_time": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "errors": 0
            }
        
        agent_metrics = self.metrics["agent_calls"][agent_name]
        agent_metrics["count"] += 1
        agent_metrics["total_time"] += execution_time
        agent_metrics["total_tokens"] += tokens_used
        agent_metrics["total_cost"] += cost
        
        if not success:
            agent_metrics["errors"] += 1
        
        self.langfuse.event(
            name=f"agent_execution_{agent_name}",
            metadata={
                "agent": agent_name,
                "task": task_description,
                "execution_time": execution_time,
                "tokens": tokens_used,
                "cost": cost,
                "success": success,
                "error": error
            }
        )

    def track_tool_usage(
        self,
        tool_name: str,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Any,
        execution_time: float
    ) -> None:
        """
        Track tool usage by an agent.
        
        Args:
            tool_name: Name of the tool
            agent_name: Agent using the tool
            input_data: Tool input
            output_data: Tool output
            execution_time: Execution time in seconds
        """
        if tool_name not in self.metrics["tool_calls"]:
            self.metrics["tool_calls"][tool_name] = {
                "count": 0,
                "total_time": 0,
                "by_agent": {}
            }
        
        tool_metrics = self.metrics["tool_calls"][tool_name]
        tool_metrics["count"] += 1
        tool_metrics["total_time"] += execution_time
        
        if agent_name not in tool_metrics["by_agent"]:
            tool_metrics["by_agent"][agent_name] = 0
        tool_metrics["by_agent"][agent_name] += 1
        
        self.langfuse.event(
            name=f"tool_usage_{tool_name}",
            metadata={
                "tool": tool_name,
                "agent": agent_name,
                "execution_time": execution_time,
                "input_size": len(str(input_data)),
                "output_size": len(str(output_data))
            }
        )

    def track_user_feedback(
        self,
        trace_id: str,
        score: float,
        comment: Optional[str] = None
    ) -> None:
        """
        Track user feedback for a trace.
        
        Args:
            trace_id: Trace to attach feedback to
            score: Feedback score (0-1)
            comment: Optional feedback comment
        """
        trace = self.active_traces.get(trace_id)
        if trace:
            trace.score(
                name="user_satisfaction",
                value=score,
                comment=comment
            )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of collected metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        agent_summary = {}
        for agent, metrics in self.metrics["agent_calls"].items():
            agent_summary[agent] = {
                "calls": metrics["count"],
                "avg_time": metrics["total_time"] / max(metrics["count"], 1),
                "avg_tokens": metrics["total_tokens"] / max(metrics["count"], 1),
                "avg_cost": metrics["total_cost"] / max(metrics["count"], 1),
                "error_rate": metrics["errors"] / max(metrics["count"], 1)
            }
        
        tool_summary = {}
        for tool, metrics in self.metrics["tool_calls"].items():
            tool_summary[tool] = {
                "calls": metrics["count"],
                "avg_time": metrics["total_time"] / max(metrics["count"], 1),
                "top_user": max(metrics["by_agent"].items(), key=lambda x: x[1])[0] if metrics["by_agent"] else None
            }
        
        return {
            "total_traces": self.metrics["total_traces"],
            "total_tokens": self.metrics["total_tokens"],
            "total_cost": self.metrics["total_cost"],
            "agents": agent_summary,
            "tools": tool_summary
        }

    def flush(self) -> None:
        """Flush all pending traces to Langfuse."""
        self.langfuse.flush()

    def shutdown(self) -> None:
        """Shutdown Langfuse client and flush remaining data."""
        self.flush()
        self.langfuse.shutdown()


@contextmanager
def trace_agent_execution(
    observer: LangfuseObserver,
    agent_name: str,
    task_description: str
):
    """
    Context manager for tracing agent execution.
    
    Args:
        observer: LangfuseObserver instance
        agent_name: Name of the agent
        task_description: Description of the task
        
    Yields:
        Trace context
    """
    start_time = time.time()
    trace = observer.create_trace(
        name=f"{agent_name}_execution",
        metadata={
            "agent": agent_name,
            "task": task_description,
            "timestamp": datetime.now().isoformat()
        }
    )
    
    tokens_before = observer.metrics["total_tokens"]
    cost_before = observer.metrics["total_cost"]
    
    try:
        yield trace
        
        execution_time = time.time() - start_time
        tokens_used = observer.metrics["total_tokens"] - tokens_before
        cost = observer.metrics["total_cost"] - cost_before
        
        observer.track_agent_execution(
            agent_name=agent_name,
            task_description=task_description,
            execution_time=execution_time,
            tokens_used=tokens_used,
            cost=cost,
            success=True
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        tokens_used = observer.metrics["total_tokens"] - tokens_before
        cost = observer.metrics["total_cost"] - cost_before
        
        observer.track_agent_execution(
            agent_name=agent_name,
            task_description=task_description,
            execution_time=execution_time,
            tokens_used=tokens_used,
            cost=cost,
            success=False,
            error=str(e)
        )
        raise
    
    finally:
        trace.update(
            output={
                "execution_time": execution_time,
                "tokens_used": tokens_used,
                "cost": cost
            }
        )


def observe_tool_call(observer: LangfuseObserver, agent_name: str):
    """
    Decorator for observing tool calls.
    
    Args:
        observer: LangfuseObserver instance
        agent_name: Name of the agent using the tool
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tool_name = func.__name__
            start_time = time.time()
            
            input_data = {
                "args": str(args)[:500],  # Truncate for storage
                "kwargs": str(kwargs)[:500]
            }
            
            try:
                result = func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                observer.track_tool_usage(
                    tool_name=tool_name,
                    agent_name=agent_name,
                    input_data=input_data,
                    output_data=str(result)[:500],  # Truncate
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                observer.track_tool_usage(
                    tool_name=tool_name,
                    agent_name=agent_name,
                    input_data=input_data,
                    output_data=f"Error: {str(e)}",
                    execution_time=execution_time
                )
                raise
        
        return wrapper
    return decorator