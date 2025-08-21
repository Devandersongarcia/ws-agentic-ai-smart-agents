"""Tests for CrewAI agents."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Any

from agents.base_agent import BaseAgent
from agents.restaurant_concierge import RestaurantConcierge
from agents.dietary_specialist import DietarySpecialist
from agents.promotions_manager import PromotionsManager


class TestBaseAgent:
    """Test suite for BaseAgent functionality."""

    @pytest.fixture
    def base_agent(self):
        """Create a BaseAgent instance."""
        with patch("config.settings.Settings"):
            return BaseAgent()

    def test_base_agent_initialization(self, base_agent):
        """Test base agent initialization."""
        assert base_agent.settings is not None
        assert base_agent.agent is None
        assert base_agent.memory is None

    def test_validate_tools(self, base_agent):
        """Test tool validation."""
        valid_tools = [Mock(), Mock()]
        base_agent.validate_tools(valid_tools)
        
        with pytest.raises(ValueError):
            base_agent.validate_tools([])
        
        with pytest.raises(ValueError):
            base_agent.validate_tools(None)

    def test_get_base_config(self, base_agent):
        """Test base configuration generation."""
        base_agent.settings.openai_api_key = "test-key"
        base_agent.settings.openai_model_name = "gpt-4o-mini"
        base_agent.settings.openai_temperature = 0.7
        base_agent.settings.crewai_max_iterations = 10
        
        config = base_agent.get_base_config()
        
        assert config["verbose"] is True
        assert config["allow_delegation"] is False
        assert config["max_iter"] == 10
        assert "llm" in config

    def test_setup_memory(self, base_agent):
        """Test memory setup."""
        with patch("crewai.memory.short_term.ShortTermMemory") as mock_memory:
            base_agent.settings.crewai_memory_type = "short_term"
            memory = base_agent.setup_memory()
            
            assert memory is not None
            mock_memory.assert_called_once()

    def test_add_knowledge_base(self, base_agent):
        """Test adding knowledge base to agent."""
        mock_agent = Mock()
        base_agent.agent = mock_agent
        
        knowledge_sources = ["source1.txt", "source2.pdf"]
        base_agent.add_knowledge_base(knowledge_sources)
        
        assert mock_agent.knowledge_base is not None


class TestRestaurantConcierge:
    """Test suite for Restaurant Concierge agent."""

    @pytest.fixture
    def concierge(self):
        """Create a RestaurantConcierge instance."""
        with patch("config.settings.Settings"):
            return RestaurantConcierge()

    def test_concierge_initialization(self, concierge):
        """Test concierge agent initialization."""
        assert concierge is not None
        assert hasattr(concierge, "settings")

    def test_create_concierge_agent(self, concierge):
        """Test creating concierge agent with tools."""
        mock_tools = [Mock(), Mock()]
        
        with patch("crewai.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            concierge.settings.concierge_role = "Test Concierge"
            concierge.settings.concierge_goal = "Test Goal"
            
            agent = concierge.create_agent(mock_tools)
            
            assert agent == mock_agent
            mock_agent_class.assert_called_once()
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs["role"] == "Test Concierge"
            assert call_kwargs["goal"] == "Test Goal"
            assert len(call_kwargs["tools"]) == 2

    def test_concierge_backstory(self, concierge):
        """Test concierge backstory generation."""
        backstory = concierge._get_backstory()
        
        assert isinstance(backstory, str)
        assert "restaurant" in backstory.lower()
        assert "recommendation" in backstory.lower()

    def test_concierge_with_memory(self, concierge):
        """Test concierge with memory enabled."""
        mock_tools = [Mock()]
        
        with patch("crewai.Agent") as mock_agent_class:
            with patch.object(concierge, "setup_memory") as mock_memory:
                mock_memory.return_value = Mock()
                
                agent = concierge.create_agent(mock_tools)
                
                mock_memory.assert_called_once()

    def test_concierge_task_execution(self, concierge):
        """Test concierge executing a recommendation task."""
        mock_agent = Mock()
        mock_agent.execute.return_value = "Restaurant recommendation result"
        concierge.agent = mock_agent
        
        result = concierge.execute_task("Find Italian restaurant")
        
        assert result == "Restaurant recommendation result"
        mock_agent.execute.assert_called_once_with("Find Italian restaurant")


class TestDietarySpecialist:
    """Test suite for Dietary Specialist agent."""

    @pytest.fixture
    def dietary_specialist(self):
        """Create a DietarySpecialist instance."""
        with patch("config.settings.Settings"):
            return DietarySpecialist()

    def test_dietary_specialist_initialization(self, dietary_specialist):
        """Test dietary specialist initialization."""
        assert dietary_specialist is not None
        assert hasattr(dietary_specialist, "settings")

    def test_create_dietary_agent(self, dietary_specialist):
        """Test creating dietary specialist agent."""
        mock_tools = [Mock(), Mock()]
        
        with patch("crewai.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            dietary_specialist.settings.dietary_role = "Dietary Expert"
            dietary_specialist.settings.dietary_goal = "Ensure food safety"
            dietary_specialist.settings.dietary_strict_mode = True
            
            agent = dietary_specialist.create_agent(mock_tools)
            
            assert agent == mock_agent
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs["role"] == "Dietary Expert"
            assert "safety" in call_kwargs["goal"].lower()

    def test_dietary_backstory(self, dietary_specialist):
        """Test dietary specialist backstory."""
        backstory = dietary_specialist._get_backstory()
        
        assert isinstance(backstory, str)
        assert "allergen" in backstory.lower() or "dietary" in backstory.lower()
        assert "safety" in backstory.lower()

    def test_strict_mode_configuration(self, dietary_specialist):
        """Test strict mode configuration for dietary specialist."""
        dietary_specialist.settings.dietary_strict_mode = True
        
        config = dietary_specialist.get_agent_specific_config()
        
        assert config["strict_mode"] is True
        assert config["fail_on_allergen"] is True

    def test_allergen_analysis_task(self, dietary_specialist):
        """Test allergen analysis task execution."""
        mock_agent = Mock()
        mock_agent.analyze_allergens.return_value = {
            "safe": False,
            "warnings": ["Contains peanuts"],
            "alternatives": ["Almond butter"]
        }
        dietary_specialist.agent = mock_agent
        
        result = dietary_specialist.check_allergens(["peanuts"], ["Pad Thai"])
        
        assert result["safe"] is False
        assert len(result["warnings"]) > 0


class TestPromotionsManager:
    """Test suite for Promotions Manager agent."""

    @pytest.fixture
    def promotions_manager(self):
        """Create a PromotionsManager instance."""
        with patch("config.settings.Settings"):
            return PromotionsManager()

    def test_promotions_manager_initialization(self, promotions_manager):
        """Test promotions manager initialization."""
        assert promotions_manager is not None
        assert hasattr(promotions_manager, "settings")

    def test_create_promotions_agent(self, promotions_manager):
        """Test creating promotions manager agent."""
        mock_tools = [Mock()]
        
        with patch("crewai.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            promotions_manager.settings.promotions_role = "Deals Expert"
            promotions_manager.settings.promotions_goal = "Find best deals"
            promotions_manager.settings.promotions_min_discount = 15
            
            agent = promotions_manager.create_agent(mock_tools)
            
            assert agent == mock_agent
            call_kwargs = mock_agent_class.call_args[1]
            assert "Deals" in call_kwargs["role"]

    def test_promotions_backstory(self, promotions_manager):
        """Test promotions manager backstory."""
        backstory = promotions_manager._get_backstory()
        
        assert isinstance(backstory, str)
        assert "discount" in backstory.lower() or "deal" in backstory.lower()
        assert "save" in backstory.lower() or "promotion" in backstory.lower()

    def test_minimum_discount_filter(self, promotions_manager):
        """Test minimum discount filtering."""
        promotions_manager.settings.promotions_min_discount = 20
        
        coupons = [
            {"discount": 10, "code": "SAVE10"},
            {"discount": 25, "code": "SAVE25"},
            {"discount": 15, "code": "SAVE15"},
            {"discount": 30, "code": "SAVE30"}
        ]
        
        filtered = promotions_manager.filter_by_minimum_discount(coupons)
        
        assert len(filtered) == 2
        assert all(c["discount"] >= 20 for c in filtered)

    def test_find_best_deals_task(self, promotions_manager):
        """Test finding best deals for a customer."""
        mock_agent = Mock()
        mock_agent.find_deals.return_value = {
            "restaurant": "Luigi's",
            "coupon_code": "SAVE30",
            "discount": 30,
            "savings": 15.00
        }
        promotions_manager.agent = mock_agent
        
        result = promotions_manager.find_best_deal(
            restaurant_id="rest-001",
            order_total=50.00
        )
        
        assert result["coupon_code"] == "SAVE30"
        assert result["discount"] == 30
        assert result["savings"] == 15.00


class TestAgentCollaboration:
    """Test suite for agent collaboration."""

    @pytest.fixture
    def agents(self):
        """Create all agent instances."""
        with patch("config.settings.Settings"):
            return {
                "concierge": RestaurantConcierge(),
                "dietary": DietarySpecialist(),
                "promotions": PromotionsManager()
            }

    def test_agent_communication(self, agents):
        """Test communication between agents."""
        mock_concierge = Mock()
        mock_concierge.recommend.return_value = {
            "restaurant_id": "rest-001",
            "menu_items": ["item-001", "item-002"]
        }
        agents["concierge"].agent = mock_concierge
        
        mock_dietary = Mock()
        mock_dietary.check.return_value = {
            "safe": True,
            "warnings": []
        }
        agents["dietary"].agent = mock_dietary
        
        recommendation = agents["concierge"].agent.recommend()
        safety_check = agents["dietary"].agent.check(recommendation["menu_items"])
        
        assert recommendation["restaurant_id"] == "rest-001"
        assert safety_check["safe"] is True

    def test_agent_delegation(self, agents):
        """Test task delegation between agents."""
        with patch("crewai.Agent") as mock_agent_class:
            for agent_type in agents.values():
                mock_agent = Mock()
                mock_agent.allow_delegation = False
                mock_agent_class.return_value = mock_agent
                agent_type.create_agent([Mock()])
                
                assert agent_type.agent.allow_delegation is False

    def test_agent_memory_sharing(self, agents):
        """Test memory sharing between agents."""
        shared_memory = Mock()
        
        for agent_type in agents.values():
            agent_type.memory = shared_memory
        
        assert agents["concierge"].memory == agents["dietary"].memory
        assert agents["dietary"].memory == agents["promotions"].memory