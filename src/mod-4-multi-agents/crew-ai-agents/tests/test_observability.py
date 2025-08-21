"""Tests for observability and monitoring."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
import json

from observability.langfuse_config import LangfuseObservability
from observability.metrics_collector import MetricsCollector


class TestLangfuseObservability:
    """Test suite for Langfuse observability."""

    @pytest.fixture
    def langfuse_obs(self):
        """Create a LangfuseObservability instance."""
        with patch("config.settings.Settings"):
            with patch("langfuse.Langfuse"):
                return LangfuseObservability()

    def test_langfuse_initialization(self, langfuse_obs):
        """Test Langfuse observability initialization."""
        assert langfuse_obs is not None
        assert hasattr(langfuse_obs, "langfuse")
        assert hasattr(langfuse_obs, "settings")
        assert hasattr(langfuse_obs, "traces")

    def test_create_trace(self, langfuse_obs):
        """Test creating a new trace."""
        mock_trace = Mock()
        mock_trace.id = "trace-001"
        langfuse_obs.langfuse.trace.return_value = mock_trace
        
        trace = langfuse_obs.create_trace(
            name="restaurant_recommendation",
            user_id="user-001",
            metadata={"cuisine": "Italian"}
        )
        
        assert trace == mock_trace
        assert "trace-001" in langfuse_obs.traces
        langfuse_obs.langfuse.trace.assert_called_once_with(
            name="restaurant_recommendation",
            user_id="user-001",
            metadata={"cuisine": "Italian"}
        )

    def test_create_span(self, langfuse_obs):
        """Test creating a span within a trace."""
        mock_trace = Mock()
        mock_span = Mock()
        mock_span.id = "span-001"
        mock_trace.span.return_value = mock_span
        
        langfuse_obs.traces["trace-001"] = mock_trace
        
        span = langfuse_obs.create_span(
            trace_id="trace-001",
            name="search_restaurants",
            input_data={"cuisine": "Italian"},
            metadata={"agent": "concierge"}
        )
        
        assert span == mock_span
        mock_trace.span.assert_called_once_with(
            name="search_restaurants",
            input={"cuisine": "Italian"},
            metadata={"agent": "concierge"}
        )

    def test_create_generation(self, langfuse_obs):
        """Test creating a generation for LLM calls."""
        mock_trace = Mock()
        mock_generation = Mock()
        mock_generation.id = "gen-001"
        mock_trace.generation.return_value = mock_generation
        
        langfuse_obs.traces["trace-001"] = mock_trace
        
        generation = langfuse_obs.create_generation(
            trace_id="trace-001",
            name="llm_call",
            model="gpt-4o-mini",
            input_text="Find Italian restaurants",
            output_text="Found 3 Italian restaurants",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        )
        
        assert generation == mock_generation
        mock_trace.generation.assert_called_once()
        call_kwargs = mock_trace.generation.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["usage"]["total_tokens"] == 30

    def test_update_span(self, langfuse_obs):
        """Test updating a span with output."""
        mock_span = Mock()
        langfuse_obs.spans = {"span-001": mock_span}
        
        langfuse_obs.update_span(
            span_id="span-001",
            output={"restaurants": ["Luigi's", "Mama's"]},
            level="INFO",
            status_message="Successfully found restaurants"
        )
        
        mock_span.update.assert_called_once_with(
            output={"restaurants": ["Luigi's", "Mama's"]},
            level="INFO",
            status_message="Successfully found restaurants"
        )

    def test_score_trace(self, langfuse_obs):
        """Test scoring a trace."""
        mock_trace = Mock()
        langfuse_obs.traces["trace-001"] = mock_trace
        
        langfuse_obs.score_trace(
            trace_id="trace-001",
            name="user_satisfaction",
            value=0.95,
            comment="User was very satisfied"
        )
        
        langfuse_obs.langfuse.score.assert_called_once_with(
            trace_id="trace-001",
            name="user_satisfaction",
            value=0.95,
            comment="User was very satisfied"
        )

    def test_event_tracking(self, langfuse_obs):
        """Test tracking custom events."""
        mock_trace = Mock()
        langfuse_obs.traces["trace-001"] = mock_trace
        
        langfuse_obs.track_event(
            trace_id="trace-001",
            name="allergen_warning",
            metadata={"allergen": "peanuts", "severity": "high"}
        )
        
        mock_trace.event.assert_called_once_with(
            name="allergen_warning",
            metadata={"allergen": "peanuts", "severity": "high"}
        )

    def test_flush_traces(self, langfuse_obs):
        """Test flushing traces to Langfuse."""
        langfuse_obs.flush()
        
        langfuse_obs.langfuse.flush.assert_called_once()

    def test_context_manager(self, langfuse_obs):
        """Test using observability as context manager."""
        with langfuse_obs.trace_context("test_operation") as trace:
            assert trace is not None
            
        langfuse_obs.langfuse.flush.assert_called()

    def test_decorator_pattern(self, langfuse_obs):
        """Test decorator for automatic tracing."""
        @langfuse_obs.observe("test_function")
        def test_function(x, y):
            return x + y
        
        with patch.object(langfuse_obs, "create_trace") as mock_trace:
            with patch.object(langfuse_obs, "create_span") as mock_span:
                mock_trace.return_value = Mock(id="trace-001")
                mock_span.return_value = Mock(id="span-001")
                
                result = test_function(2, 3)
                
                assert result == 5
                mock_trace.assert_called_once()
                mock_span.assert_called_once()

    def test_error_handling(self, langfuse_obs):
        """Test error handling in observability."""
        mock_trace = Mock()
        mock_span = Mock()
        mock_trace.span.return_value = mock_span
        langfuse_obs.traces["trace-001"] = mock_trace
        
        with patch.object(langfuse_obs, "update_span") as mock_update:
            try:
                span = langfuse_obs.create_span("trace-001", "error_test")
                raise ValueError("Test error")
            except ValueError:
                langfuse_obs.handle_error(
                    span_id=span.id,
                    error="Test error",
                    level="ERROR"
                )
            
            mock_update.assert_called_with(
                span_id=span.id,
                level="ERROR",
                status_message="Test error"
            )


class TestMetricsCollector:
    """Test suite for metrics collection."""

    @pytest.fixture
    def metrics_collector(self):
        """Create a MetricsCollector instance."""
        with patch("config.settings.Settings"):
            return MetricsCollector()

    def test_metrics_initialization(self, metrics_collector):
        """Test metrics collector initialization."""
        assert metrics_collector is not None
        assert hasattr(metrics_collector, "metrics")
        assert hasattr(metrics_collector, "settings")

    def test_record_agent_execution(self, metrics_collector):
        """Test recording agent execution metrics."""
        metrics_collector.record_agent_execution(
            agent_name="Restaurant Concierge",
            task_name="Find Restaurant",
            execution_time=2.5,
            tokens_used=150,
            success=True
        )
        
        metrics = metrics_collector.get_agent_metrics("Restaurant Concierge")
        assert metrics["total_executions"] == 1
        assert metrics["total_tokens"] == 150
        assert metrics["avg_execution_time"] == 2.5
        assert metrics["success_rate"] == 1.0

    def test_record_tool_usage(self, metrics_collector):
        """Test recording tool usage metrics."""
        metrics_collector.record_tool_usage(
            tool_name="RestaurantSearch",
            execution_time=0.5,
            success=True
        )
        
        metrics_collector.record_tool_usage(
            tool_name="RestaurantSearch",
            execution_time=0.7,
            success=True
        )
        
        metrics = metrics_collector.get_tool_metrics("RestaurantSearch")
        assert metrics["usage_count"] == 2
        assert metrics["avg_execution_time"] == 0.6
        assert metrics["success_rate"] == 1.0

    def test_record_crew_execution(self, metrics_collector):
        """Test recording crew execution metrics."""
        metrics_collector.record_crew_execution(
            crew_name="RestaurantRecommendation",
            total_time=10.5,
            tasks_completed=4,
            tokens_used=500,
            cost=0.01,
            success=True
        )
        
        metrics = metrics_collector.get_crew_metrics("RestaurantRecommendation")
        assert metrics["total_executions"] == 1
        assert metrics["avg_time"] == 10.5
        assert metrics["total_tokens"] == 500
        assert metrics["total_cost"] == 0.01

    def test_record_error(self, metrics_collector):
        """Test recording errors."""
        metrics_collector.record_error(
            component="DietarySpecialist",
            error_type="AllergenCheckError",
            error_message="Failed to check allergens"
        )
        
        errors = metrics_collector.get_errors("DietarySpecialist")
        assert len(errors) == 1
        assert errors[0]["error_type"] == "AllergenCheckError"

    def test_calculate_cost(self, metrics_collector):
        """Test cost calculation for tokens."""
        metrics_collector.settings.openai_model_name = "gpt-4o-mini"
        
        cost = metrics_collector.calculate_cost(
            prompt_tokens=100,
            completion_tokens=50,
            model="gpt-4o-mini"
        )
        
        assert cost > 0
        assert isinstance(cost, float)

    def test_get_summary_metrics(self, metrics_collector):
        """Test getting summary metrics."""
        metrics_collector.record_agent_execution(
            "Agent1", "Task1", 1.0, 100, True
        )
        metrics_collector.record_agent_execution(
            "Agent2", "Task2", 2.0, 200, True
        )
        metrics_collector.record_tool_usage(
            "Tool1", 0.5, True
        )
        
        summary = metrics_collector.get_summary()
        
        assert summary["total_agent_executions"] == 2
        assert summary["total_tool_uses"] == 1
        assert summary["total_tokens"] == 300

    def test_reset_metrics(self, metrics_collector):
        """Test resetting metrics."""
        metrics_collector.record_agent_execution(
            "Agent1", "Task1", 1.0, 100, True
        )
        
        metrics_collector.reset()
        
        metrics = metrics_collector.get_agent_metrics("Agent1")
        assert metrics["total_executions"] == 0

    def test_export_metrics(self, metrics_collector):
        """Test exporting metrics to JSON."""
        metrics_collector.record_agent_execution(
            "Agent1", "Task1", 1.0, 100, True
        )
        metrics_collector.record_tool_usage(
            "Tool1", 0.5, True
        )
        
        exported = metrics_collector.export_json()
        
        assert isinstance(exported, str)
        data = json.loads(exported)
        assert "agents" in data
        assert "tools" in data
        assert "timestamp" in data

    def test_metrics_aggregation(self, metrics_collector):
        """Test metrics aggregation over time."""
        for i in range(10):
            metrics_collector.record_agent_execution(
                "Agent1", f"Task{i}", 1.0 + i * 0.1, 100 + i * 10, True
            )
        
        metrics = metrics_collector.get_agent_metrics("Agent1")
        assert metrics["total_executions"] == 10
        assert metrics["total_tokens"] == 1450
        assert metrics["avg_execution_time"] == pytest.approx(1.45, 0.01)

    def test_percentile_calculations(self, metrics_collector):
        """Test percentile calculations for metrics."""
        execution_times = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for time in execution_times:
            metrics_collector.record_agent_execution(
                "Agent1", "Task", time, 100, True
            )
        
        percentiles = metrics_collector.get_execution_percentiles("Agent1")
        assert percentiles["p50"] == 3.0
        assert percentiles["p90"] >= 4.0
        assert percentiles["p99"] <= 5.0


class TestObservabilityIntegration:
    """Test suite for observability integration."""

    @pytest.fixture
    def integrated_system(self):
        """Create integrated observability system."""
        with patch("config.settings.Settings"):
            with patch("langfuse.Langfuse"):
                return {
                    "langfuse": LangfuseObservability(),
                    "metrics": MetricsCollector()
                }

    def test_integrated_tracing_and_metrics(self, integrated_system):
        """Test integrated tracing and metrics collection."""
        langfuse = integrated_system["langfuse"]
        metrics = integrated_system["metrics"]
        
        trace = langfuse.create_trace("test_operation")
        span = langfuse.create_span(trace.id, "agent_execution")
        
        start_time = datetime.now()
        metrics.record_agent_execution(
            "TestAgent", "TestTask", 2.5, 150, True
        )
        
        langfuse.update_span(
            span.id,
            output={"result": "success"},
            level="INFO"
        )
        
        agent_metrics = metrics.get_agent_metrics("TestAgent")
        assert agent_metrics["total_executions"] == 1
        assert agent_metrics["total_tokens"] == 150

    def test_error_tracking_integration(self, integrated_system):
        """Test integrated error tracking."""
        langfuse = integrated_system["langfuse"]
        metrics = integrated_system["metrics"]
        
        trace = langfuse.create_trace("error_operation")
        span = langfuse.create_span(trace.id, "failing_task")
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            langfuse.handle_error(span.id, str(e), "ERROR")
            metrics.record_error(
                "TestComponent",
                type(e).__name__,
                str(e)
            )
        
        errors = metrics.get_errors("TestComponent")
        assert len(errors) == 1
        assert errors[0]["error_type"] == "ValueError"

    def test_cost_tracking_integration(self, integrated_system):
        """Test integrated cost tracking."""
        langfuse = integrated_system["langfuse"]
        metrics = integrated_system["metrics"]
        
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
        
        generation = langfuse.create_generation(
            trace_id="trace-001",
            name="llm_call",
            model="gpt-4o-mini",
            input_text="test input",
            output_text="test output",
            usage=usage
        )
        
        cost = metrics.calculate_cost(
            usage["prompt_tokens"],
            usage["completion_tokens"],
            "gpt-4o-mini"
        )
        
        metrics.record_crew_execution(
            "TestCrew",
            10.0,
            1,
            usage["total_tokens"],
            cost,
            True
        )
        
        crew_metrics = metrics.get_crew_metrics("TestCrew")
        assert crew_metrics["total_cost"] == cost