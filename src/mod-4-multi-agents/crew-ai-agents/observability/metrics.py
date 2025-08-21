"""
Metrics collection for agent performance and system monitoring.
Tracks key performance indicators for optimization.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class AgentMetrics:
    """Metrics for individual agent performance."""
    
    name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_satisfaction: float = 0.0
    satisfaction_count: int = 0
    last_execution: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class ToolMetrics:
    """Metrics for tool usage."""
    
    name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    average_response_size: float = 0.0
    calls_by_agent: Dict[str, int] = field(default_factory=dict)
    last_called: Optional[datetime] = None


@dataclass
class SystemMetrics:
    """Overall system performance metrics."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    peak_tokens_per_minute: int = 0
    total_cost_today: float = 0.0
    active_sessions: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


class MetricsCollector:
    """
    Collects and aggregates metrics for the multi-agent system.
    Provides insights for performance optimization and monitoring.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.tool_metrics: Dict[str, ToolMetrics] = {}
        self.system_metrics = SystemMetrics()
        self.time_series_data = defaultdict(list)
        self.session_start = datetime.now()

    def record_agent_execution(
        self,
        agent_name: str,
        execution_time: float,
        tokens: int,
        cost: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Record metrics for an agent execution.
        
        Args:
            agent_name: Name of the agent
            execution_time: Time taken in seconds
            tokens: Tokens consumed
            cost: Cost in dollars
            success: Whether execution succeeded
            error: Error message if failed
        """
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(name=agent_name)
        
        metrics = self.agent_metrics[agent_name]
        metrics.total_executions += 1
        metrics.total_execution_time += execution_time
        metrics.total_tokens += tokens
        metrics.total_cost += cost
        metrics.last_execution = datetime.now()
        
        if success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1
            if error:
                metrics.errors.append(f"{datetime.now().isoformat()}: {error}")
                metrics.errors = metrics.errors[-10:]
        
        self.time_series_data[f"agent_{agent_name}_tokens"].append({
            "timestamp": datetime.now(),
            "value": tokens
        })

    def record_tool_call(
        self,
        tool_name: str,
        agent_name: str,
        execution_time: float,
        response_size: int,
        success: bool = True
    ) -> None:
        """
        Record metrics for a tool call.
        
        Args:
            tool_name: Name of the tool
            agent_name: Agent making the call
            execution_time: Time taken in seconds
            response_size: Size of response in bytes
            success: Whether call succeeded
        """
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = ToolMetrics(name=tool_name)
        
        metrics = self.tool_metrics[tool_name]
        metrics.total_calls += 1
        metrics.total_execution_time += execution_time
        metrics.last_called = datetime.now()
        
        metrics.average_response_size = (
            (metrics.average_response_size * (metrics.total_calls - 1) + response_size)
            / metrics.total_calls
        )
        
        if success:
            metrics.successful_calls += 1
        else:
            metrics.failed_calls += 1
        
        if agent_name not in metrics.calls_by_agent:
            metrics.calls_by_agent[agent_name] = 0
        metrics.calls_by_agent[agent_name] += 1

    def record_user_satisfaction(
        self,
        agent_name: str,
        satisfaction_score: float
    ) -> None:
        """
        Record user satisfaction score for an agent.
        
        Args:
            agent_name: Name of the agent
            satisfaction_score: Score from 0 to 1
        """
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(name=agent_name)
        
        metrics = self.agent_metrics[agent_name]
        metrics.satisfaction_count += 1
        
        metrics.average_satisfaction = (
            (metrics.average_satisfaction * (metrics.satisfaction_count - 1) + satisfaction_score)
            / metrics.satisfaction_count
        )

    def record_system_request(
        self,
        response_time: float,
        success: bool = True
    ) -> None:
        """
        Record a system-level request.
        
        Args:
            response_time: Total response time in seconds
            success: Whether request succeeded
        """
        self.system_metrics.total_requests += 1
        self.system_metrics.total_response_time += response_time
        
        if success:
            self.system_metrics.successful_requests += 1
        else:
            self.system_metrics.failed_requests += 1

    def record_cache_access(self, hit: bool) -> None:
        """
        Record cache access.
        
        Args:
            hit: Whether it was a cache hit
        """
        if hit:
            self.system_metrics.cache_hits += 1
        else:
            self.system_metrics.cache_misses += 1

    def get_agent_summary(self, agent_name: str) -> Dict[str, Any]:
        """
        Get summary metrics for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Summary dictionary
        """
        if agent_name not in self.agent_metrics:
            return {"error": f"No metrics for agent: {agent_name}"}
        
        metrics = self.agent_metrics[agent_name]
        
        return {
            "name": agent_name,
            "total_executions": metrics.total_executions,
            "success_rate": (
                metrics.successful_executions / max(metrics.total_executions, 1)
            ),
            "average_execution_time": (
                metrics.total_execution_time / max(metrics.total_executions, 1)
            ),
            "average_tokens": (
                metrics.total_tokens / max(metrics.total_executions, 1)
            ),
            "average_cost": (
                metrics.total_cost / max(metrics.total_executions, 1)
            ),
            "total_cost": metrics.total_cost,
            "average_satisfaction": metrics.average_satisfaction,
            "last_execution": metrics.last_execution.isoformat() if metrics.last_execution else None,
            "recent_errors": metrics.errors[-3:]  # Last 3 errors
        }

    def get_tool_summary(self, tool_name: str) -> Dict[str, Any]:
        """
        Get summary metrics for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Summary dictionary
        """
        if tool_name not in self.tool_metrics:
            return {"error": f"No metrics for tool: {tool_name}"}
        
        metrics = self.tool_metrics[tool_name]
        
        return {
            "name": tool_name,
            "total_calls": metrics.total_calls,
            "success_rate": (
                metrics.successful_calls / max(metrics.total_calls, 1)
            ),
            "average_execution_time": (
                metrics.total_execution_time / max(metrics.total_calls, 1)
            ),
            "average_response_size": metrics.average_response_size,
            "top_users": sorted(
                metrics.calls_by_agent.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3],
            "last_called": metrics.last_called.isoformat() if metrics.last_called else None
        }

    def get_system_summary(self) -> Dict[str, Any]:
        """
        Get overall system metrics summary.
        
        Returns:
            System summary dictionary
        """
        uptime = datetime.now() - self.session_start
        
        return {
            "uptime": str(uptime),
            "total_requests": self.system_metrics.total_requests,
            "success_rate": (
                self.system_metrics.successful_requests 
                / max(self.system_metrics.total_requests, 1)
            ),
            "average_response_time": (
                self.system_metrics.total_response_time 
                / max(self.system_metrics.total_requests, 1)
            ),
            "cache_hit_rate": (
                self.system_metrics.cache_hits 
                / max(self.system_metrics.cache_hits + self.system_metrics.cache_misses, 1)
            ),
            "total_agents": len(self.agent_metrics),
            "total_tools": len(self.tool_metrics),
            "most_active_agent": (
                max(
                    self.agent_metrics.items(),
                    key=lambda x: x[1].total_executions
                )[0] if self.agent_metrics else None
            ),
            "most_used_tool": (
                max(
                    self.tool_metrics.items(),
                    key=lambda x: x[1].total_calls
                )[0] if self.tool_metrics else None
            )
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Returns:
            Performance report dictionary
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_summary(),
            "agents": {
                name: self.get_agent_summary(name)
                for name in self.agent_metrics
            },
            "tools": {
                name: self.get_tool_summary(name)
                for name in self.tool_metrics
            },
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """
        Generate performance optimization recommendations.
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        for name, metrics in self.agent_metrics.items():
            if metrics.total_executions > 10:
                success_rate = metrics.successful_executions / metrics.total_executions
                if success_rate < 0.8:
                    recommendations.append(
                        f"Agent '{name}' has low success rate ({success_rate:.1%}). "
                        "Consider reviewing error logs and adjusting prompts."
                    )
                
                avg_time = metrics.total_execution_time / metrics.total_executions
                if avg_time > 30:
                    recommendations.append(
                        f"Agent '{name}' has high average execution time ({avg_time:.1f}s). "
                        "Consider optimizing task complexity or tools."
                    )
        
        if self.system_metrics.cache_hits + self.system_metrics.cache_misses > 100:
            cache_hit_rate = (
                self.system_metrics.cache_hits 
                / (self.system_metrics.cache_hits + self.system_metrics.cache_misses)
            )
            if cache_hit_rate < 0.5:
                recommendations.append(
                    f"Low cache hit rate ({cache_hit_rate:.1%}). "
                    "Consider increasing cache TTL or improving cache key strategy."
                )
        
        for name, metrics in self.tool_metrics.items():
            if metrics.total_calls < 5 and len(self.agent_metrics) > 0:
                recommendations.append(
                    f"Tool '{name}' is underutilized ({metrics.total_calls} calls). "
                    "Consider whether it's needed or needs better integration."
                )
        
        if not recommendations:
            recommendations.append("System performing well. No immediate optimizations needed.")
        
        return recommendations