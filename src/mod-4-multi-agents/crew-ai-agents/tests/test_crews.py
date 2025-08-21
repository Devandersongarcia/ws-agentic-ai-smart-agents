"""Tests for crew orchestration."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from crews.restaurant_crew import RestaurantRecommendationCrew
from crews.crew_factory import CrewFactory


class TestRestaurantRecommendationCrew:
    """Test suite for Restaurant Recommendation Crew."""

    @pytest.fixture
    def crew(self):
        """Create a RestaurantRecommendationCrew instance."""
        with patch("config.settings.Settings"):
            with patch("agents.restaurant_concierge.RestaurantConcierge"):
                with patch("agents.dietary_specialist.DietarySpecialist"):
                    with patch("agents.promotions_manager.PromotionsManager"):
                        return RestaurantRecommendationCrew()

    def test_crew_initialization(self, crew):
        """Test crew initialization."""
        assert crew is not None
        assert hasattr(crew, "agents")
        assert hasattr(crew, "tools")
        assert hasattr(crew, "crew")

    def test_setup_agents(self, crew):
        """Test setting up all agents."""
        crew.setup_agents()
        
        assert "concierge" in crew.agents
        assert "dietary_specialist" in crew.agents
        assert "promotions_manager" in crew.agents
        assert len(crew.agents) == 3

    def test_setup_tools(self, crew):
        """Test setting up all tools."""
        crew.setup_tools()
        
        assert "restaurant_search" in crew.tools
        assert "menu_analyzer" in crew.tools
        assert "allergen_checker" in crew.tools
        assert "coupon_finder" in crew.tools
        assert "recommendation_engine" in crew.tools
        assert len(crew.tools) == 5

    def test_create_tasks(self, crew):
        """Test creating crew tasks."""
        crew.setup_agents()
        crew.setup_tools()
        
        customer_request = {
            "cuisine": "Italian",
            "dietary": ["vegetarian"],
            "budget": "$$",
            "party_size": 4
        }
        
        tasks = crew.create_tasks(customer_request)
        
        assert len(tasks) == 4
        assert tasks[0].description is not None
        assert tasks[0].agent is not None
        assert tasks[0].tools is not None

    def test_task_dependencies(self, crew):
        """Test task dependency configuration."""
        crew.setup_agents()
        crew.setup_tools()
        
        customer_request = {"cuisine": "Japanese"}
        tasks = crew.create_tasks(customer_request)
        
        assert tasks[1].context == [tasks[0]]
        assert tasks[2].context == [tasks[0]]
        assert tasks[3].context == [tasks[0], tasks[1], tasks[2]]

    def test_create_crew(self, crew):
        """Test creating the crew with all components."""
        with patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance
            
            crew.setup_agents()
            crew.setup_tools()
            customer_request = {"cuisine": "Mexican"}
            
            crew_instance = crew.create_crew(customer_request)
            
            assert crew_instance == mock_crew_instance
            mock_crew_class.assert_called_once()
            call_kwargs = mock_crew_class.call_args[1]
            assert len(call_kwargs["agents"]) == 3
            assert len(call_kwargs["tasks"]) == 4
            assert call_kwargs["verbose"] is True

    def test_execute_crew(self, crew):
        """Test executing the crew."""
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.return_value = {
            "recommendation": "Luigi's Restaurant",
            "safety_check": "All clear",
            "best_deal": "20% off with SAVE20"
        }
        crew.crew = mock_crew_instance
        
        result = crew.execute()
        
        assert result["recommendation"] == "Luigi's Restaurant"
        assert result["safety_check"] == "All clear"
        assert result["best_deal"] == "20% off with SAVE20"
        mock_crew_instance.kickoff.assert_called_once()

    def test_process_recommendation(self, crew):
        """Test processing a complete recommendation request."""
        customer_request = {
            "cuisine": "Thai",
            "dietary": ["gluten-free"],
            "allergens": ["peanuts"],
            "budget": "$$$",
            "location": "downtown"
        }
        
        with patch.object(crew, "create_crew") as mock_create:
            with patch.object(crew, "execute") as mock_execute:
                mock_crew_instance = Mock()
                mock_create.return_value = mock_crew_instance
                mock_execute.return_value = {
                    "status": "success",
                    "recommendations": [{"restaurant": "Thai Palace"}]
                }
                
                result = crew.process_recommendation(customer_request)
                
                assert result["status"] == "success"
                assert len(result["recommendations"]) == 1
                mock_create.assert_called_once_with(customer_request)
                mock_execute.assert_called_once()

    def test_memory_integration(self, crew):
        """Test crew memory integration."""
        crew.setup_agents()
        
        with patch("crewai.memory.short_term.ShortTermMemory") as mock_memory:
            mock_memory_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            
            crew.setup_memory()
            
            assert crew.memory is not None
            assert crew.memory == mock_memory_instance

    def test_knowledge_base_integration(self, crew):
        """Test crew knowledge base integration."""
        crew.setup_agents()
        
        knowledge_sources = [
            "restaurants.json",
            "menus.pdf",
            "allergen_guide.docx"
        ]
        
        crew.add_knowledge_base(knowledge_sources)
        
        for agent in crew.agents.values():
            assert hasattr(agent, "knowledge_base")


class TestCrewFactory:
    """Test suite for Crew Factory."""

    @pytest.fixture
    def factory(self):
        """Create a CrewFactory instance."""
        with patch("config.settings.Settings"):
            return CrewFactory()

    def test_factory_initialization(self, factory):
        """Test crew factory initialization."""
        assert factory is not None
        assert hasattr(factory, "settings")
        assert hasattr(factory, "crews")

    def test_register_crew(self, factory):
        """Test registering a new crew type."""
        mock_crew_class = Mock()
        
        factory.register_crew("custom_crew", mock_crew_class)
        
        assert "custom_crew" in factory.crews
        assert factory.crews["custom_crew"] == mock_crew_class

    def test_create_restaurant_crew(self, factory):
        """Test creating a restaurant recommendation crew."""
        with patch("crews.restaurant_crew.RestaurantRecommendationCrew") as mock_crew:
            mock_crew_instance = Mock()
            mock_crew.return_value = mock_crew_instance
            
            crew = factory.create_crew("restaurant_recommendation")
            
            assert crew == mock_crew_instance
            mock_crew.assert_called_once()

    def test_create_unknown_crew(self, factory):
        """Test creating an unknown crew type."""
        with pytest.raises(ValueError) as exc_info:
            factory.create_crew("unknown_crew")
        
        assert "Unknown crew type" in str(exc_info.value)

    def test_list_available_crews(self, factory):
        """Test listing available crew types."""
        factory.register_crew("crew1", Mock())
        factory.register_crew("crew2", Mock())
        
        available = factory.list_available_crews()
        
        assert "crew1" in available
        assert "crew2" in available
        assert "restaurant_recommendation" in available

    def test_create_crew_with_config(self, factory):
        """Test creating crew with custom configuration."""
        config = {
            "process_type": "hierarchical",
            "max_iterations": 15,
            "memory_type": "long_term"
        }
        
        with patch("crews.restaurant_crew.RestaurantRecommendationCrew") as mock_crew:
            mock_crew_instance = Mock()
            mock_crew.return_value = mock_crew_instance
            
            crew = factory.create_crew("restaurant_recommendation", config)
            
            assert crew == mock_crew_instance
            mock_crew.assert_called_once_with(config)

    def test_crew_caching(self, factory):
        """Test crew instance caching."""
        factory.enable_caching = True
        
        with patch("crews.restaurant_crew.RestaurantRecommendationCrew") as mock_crew:
            mock_crew_instance = Mock()
            mock_crew.return_value = mock_crew_instance
            
            crew1 = factory.create_crew("restaurant_recommendation")
            crew2 = factory.create_crew("restaurant_recommendation")
            
            assert crew1 == crew2
            mock_crew.assert_called_once()


class TestCrewOrchestration:
    """Test suite for advanced crew orchestration."""

    @pytest.fixture
    def orchestrator(self):
        """Create crew orchestration components."""
        with patch("config.settings.Settings"):
            return {
                "factory": CrewFactory(),
                "crew": RestaurantRecommendationCrew()
            }

    def test_sequential_task_execution(self, orchestrator):
        """Test sequential task execution in crew."""
        crew = orchestrator["crew"]
        crew.settings.crewai_process_type = "sequential"
        
        with patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance
            
            crew.setup_agents()
            crew.setup_tools()
            crew.create_crew({"cuisine": "Italian"})
            
            call_kwargs = mock_crew_class.call_args[1]
            assert call_kwargs["process"] == "sequential"

    def test_hierarchical_task_execution(self, orchestrator):
        """Test hierarchical task execution in crew."""
        crew = orchestrator["crew"]
        crew.settings.crewai_process_type = "hierarchical"
        
        with patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance
            
            crew.setup_agents()
            crew.setup_tools()
            crew.create_crew({"cuisine": "Japanese"})
            
            call_kwargs = mock_crew_class.call_args[1]
            assert call_kwargs["process"] == "hierarchical"
            assert "manager_llm" in call_kwargs

    def test_crew_with_callbacks(self, orchestrator):
        """Test crew with callback functions."""
        crew = orchestrator["crew"]
        
        task_complete_callback = Mock()
        step_callback = Mock()
        
        crew.add_callbacks(
            on_task_complete=task_complete_callback,
            on_step=step_callback
        )
        
        with patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance
            
            crew.setup_agents()
            crew.setup_tools()
            crew.create_crew({"cuisine": "Mexican"})
            
            call_kwargs = mock_crew_class.call_args[1]
            assert call_kwargs["task_callback"] == task_complete_callback
            assert call_kwargs["step_callback"] == step_callback

    def test_crew_error_handling(self, orchestrator):
        """Test crew error handling."""
        crew = orchestrator["crew"]
        
        with patch.object(crew, "create_crew") as mock_create:
            mock_create.side_effect = Exception("Crew creation failed")
            
            result = crew.process_recommendation({"cuisine": "Indian"})
            
            assert result["status"] == "error"
            assert "Crew creation failed" in result["error"]

    def test_crew_with_custom_llm(self, orchestrator):
        """Test crew with custom LLM configuration."""
        crew = orchestrator["crew"]
        
        custom_llm_config = {
            "model": "gpt-4o",
            "temperature": 0.5,
            "max_tokens": 3000
        }
        
        crew.set_custom_llm(custom_llm_config)
        
        with patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance
            
            crew.setup_agents()
            crew.setup_tools()
            crew.create_crew({"cuisine": "Chinese"})
            
            for agent in crew.agents.values():
                assert agent.llm_config == custom_llm_config

    def test_crew_telemetry(self, orchestrator):
        """Test crew telemetry and metrics."""
        crew = orchestrator["crew"]
        
        with patch("crewai.telemetry.Telemetry") as mock_telemetry:
            mock_telemetry_instance = Mock()
            mock_telemetry.return_value = mock_telemetry_instance
            
            crew.enable_telemetry()
            
            assert crew.telemetry == mock_telemetry_instance
            mock_telemetry_instance.start.assert_called_once()