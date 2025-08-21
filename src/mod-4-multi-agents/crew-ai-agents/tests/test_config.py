"""Tests for configuration module."""

import os
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from config.settings import Settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_settings_loads_from_env(self):
        """Test that settings properly load from environment variables."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-supabase-key"
        }):
            settings = Settings()
            assert settings.openai_api_key == "test-key"
            assert settings.supabase_url == "https://test.supabase.co"
            assert settings.supabase_key == "test-supabase-key"

    def test_settings_validation_error_missing_required(self):
        """Test that validation error occurs when required fields are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_openai_config_properties(self):
        """Test OpenAI configuration properties."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_MODEL_NAME": "gpt-4o-mini",
            "OPENAI_TEMPERATURE": "0.7",
            "OPENAI_MAX_TOKENS": "2000",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        }):
            settings = Settings()
            config = settings.openai_config
            assert config["api_key"] == "test-key"
            assert config["model"] == "gpt-4o-mini"
            assert config["temperature"] == 0.7
            assert config["max_tokens"] == 2000

    def test_supabase_config_properties(self):
        """Test Supabase configuration properties."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-supabase-key",
            "SUPABASE_SERVICE_ROLE_KEY": "test-service-key"
        }):
            settings = Settings()
            config = settings.supabase_config
            assert config["url"] == "https://test.supabase.co"
            assert config["key"] == "test-supabase-key"
            assert config["service_role_key"] == "test-service-key"

    def test_langfuse_config_properties(self):
        """Test Langfuse configuration properties."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            settings = Settings()
            config = settings.langfuse_config
            assert config["public_key"] == "pk-test"
            assert config["secret_key"] == "sk-test"
            assert config["host"] == "https://test.langfuse.com"

    def test_crewai_config_properties(self):
        """Test CrewAI configuration properties."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "CREWAI_MEMORY_TYPE": "long_term",
            "CREWAI_MAX_ITERATIONS": "15",
            "CREWAI_PROCESS_TYPE": "hierarchical"
        }):
            settings = Settings()
            config = settings.crewai_config
            assert config["memory_type"] == "long_term"
            assert config["max_iterations"] == 15
            assert config["process_type"] == "hierarchical"

    def test_agent_configs(self):
        """Test agent-specific configurations."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "CONCIERGE_ROLE": "Test Concierge",
            "DIETARY_ROLE": "Test Dietary",
            "PROMOTIONS_ROLE": "Test Promotions"
        }):
            settings = Settings()
            assert settings.concierge_role == "Test Concierge"
            assert settings.dietary_role == "Test Dietary"
            assert settings.promotions_role == "Test Promotions"

    def test_ingestion_config_properties(self):
        """Test ingestion pipeline configuration."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "INGESTION_BATCH_SIZE": "20",
            "INGESTION_CHUNK_SIZE": "1000",
            "INGESTION_CHUNK_OVERLAP": "100"
        }):
            settings = Settings()
            config = settings.ingestion_config
            assert config["batch_size"] == 20
            assert config["chunk_size"] == 1000
            assert config["chunk_overlap"] == 100

    def test_cache_configuration(self):
        """Test cache configuration settings."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "CACHE_ENABLED": "true",
            "CACHE_TTL_SECONDS": "7200",
            "CACHE_TYPE": "redis"
        }):
            settings = Settings()
            assert settings.cache_enabled is True
            assert settings.cache_ttl_seconds == 7200
            assert settings.cache_type == "redis"

    def test_feature_flags(self):
        """Test feature flag configurations."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "FEATURE_ADVANCED_REASONING": "false",
            "FEATURE_MULTI_AGENT_COLLABORATION": "true"
        }):
            settings = Settings()
            assert settings.feature_advanced_reasoning is False
            assert settings.feature_multi_agent_collaboration is True