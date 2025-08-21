"""
Settings management using Pydantic for type safety and validation.
Centralizes all configuration from environment variables.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Provides type validation and default values for all configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model_name: str = Field(default="gpt-4o-mini", description="LLM model to use")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="Embedding model"
    )
    openai_embedding_dimension: int = Field(default=1536, description="Embedding dimensions")
    openai_max_tokens: int = Field(default=2000, description="Max tokens per response")
    openai_temperature: float = Field(default=0.7, description="Model temperature")

    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anonymous key")
    supabase_service_role_key: Optional[str] = Field(
        default=None, description="Supabase service role key"
    )
    supabase_db_url: str = Field(..., description="PostgreSQL connection string")

    supabase_collection_menus: str = Field(default="menus", description="Menus collection name")
    supabase_collection_restaurants: str = Field(
        default="restaurants", description="Restaurants collection name"
    )
    supabase_collection_coupons: str = Field(
        default="coupons", description="Coupons collection name"
    )
    supabase_collection_allergens: str = Field(
        default="allergens", description="Allergens collection name"
    )

    langfuse_public_key: str = Field(..., description="Langfuse public key")
    langfuse_secret_key: str = Field(..., description="Langfuse secret key")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com", description="Langfuse host URL"
    )
    langfuse_release: str = Field(default="v1.0.0", description="Application version")
    langfuse_debug: bool = Field(default=False, description="Enable debug logging")
    langfuse_flush_interval: int = Field(default=30, description="Trace flush interval")

    crewai_api_key: Optional[str] = Field(default=None, description="CrewAI+ API key")
    crewai_telemetry_enabled: bool = Field(default=True, description="Enable telemetry")
    crewai_log_level: str = Field(default="INFO", description="Logging level")
    crewai_memory_type: str = Field(default="short_term", description="Memory type")
    crewai_max_iterations: int = Field(default=10, description="Max agent iterations")
    crewai_process_type: str = Field(default="sequential", description="Process type")

    concierge_role: str = Field(
        default="Restaurant Recommendation Specialist", description="Concierge role"
    )
    concierge_goal: str = Field(
        default="Help customers find the perfect restaurant", description="Concierge goal"
    )
    concierge_max_retry: int = Field(default=3, description="Max retries for concierge")

    dietary_role: str = Field(
        default="Food Safety and Allergen Expert", description="Dietary specialist role"
    )
    dietary_goal: str = Field(
        default="Ensure customer safety by analyzing allergen information",
        description="Dietary goal",
    )
    dietary_strict_mode: bool = Field(default=True, description="Strict allergen checking")

    promotions_role: str = Field(
        default="Deals and Discount Optimizer", description="Promotions manager role"
    )
    promotions_goal: str = Field(
        default="Find the best available deals", description="Promotions goal"
    )
    promotions_min_discount: int = Field(default=10, description="Minimum discount percentage")

    ingestion_batch_size: int = Field(default=10, description="Documents per batch")
    ingestion_chunk_size: int = Field(default=500, description="Tokens per chunk")
    ingestion_chunk_overlap: int = Field(default=50, description="Token overlap")
    ingestion_max_workers: int = Field(default=4, description="Parallel workers")
    docling_use_gpu: bool = Field(default=False, description="Use GPU for Docling")
    docling_ocr_enabled: bool = Field(default=True, description="Enable OCR")

    app_env: str = Field(default="development", description="Environment")
    app_debug: bool = Field(default=True, description="Debug mode")
    app_host: str = Field(default="localhost", description="Application host")
    app_port: int = Field(default=8000, description="Application port")
    app_log_level: str = Field(default="INFO", description="Log level")
    app_log_format: str = Field(default="json", description="Log format")

    data_storage_path: Path = Field(
        default=Path("../../../storage"), description="Storage directory"
    )
    data_output_path: Path = Field(default=Path("./output"), description="Output directory")
    data_cache_path: Path = Field(default=Path("./cache"), description="Cache directory")
    data_logs_path: Path = Field(default=Path("./logs"), description="Logs directory")

    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(default=60, description="Requests per minute")
    rate_limit_tokens_per_minute: int = Field(default=40000, description="Tokens per minute")

    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    cache_type: str = Field(default="memory", description="Cache type")

    feature_advanced_reasoning: bool = Field(default=True, description="Advanced reasoning")
    feature_multi_agent_collaboration: bool = Field(
        default=True, description="Multi-agent collaboration"
    )
    feature_user_feedback_loop: bool = Field(default=True, description="User feedback")

    @field_validator("data_storage_path", "data_output_path", "data_cache_path", "data_logs_path")
    @classmethod
    def resolve_paths(cls, v: Path) -> Path:
        """
        Resolve relative paths to absolute paths.
        
        Args:
            v: Path to resolve
            
        Returns:
            Absolute path
        """
        if not v.is_absolute():
            base_dir = Path(__file__).parent.parent
            return (base_dir / v).resolve()
        return v

    @field_validator("openai_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """
        Validate temperature is within valid range.
        
        Args:
            v: Temperature value
            
        Returns:
            Validated temperature
            
        Raises:
            ValueError: If temperature is out of range
        """
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @field_validator("app_log_level", "crewai_log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        Validate log level is valid.
        
        Args:
            v: Log level string
            
        Returns:
            Uppercase log level
            
        Raises:
            ValueError: If log level is invalid
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper

    def get_absolute_storage_path(self) -> Path:
        """
        Get absolute path to storage directory.
        
        Returns:
            Absolute path to storage directory
        """
        return self.data_storage_path.resolve()

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for path in [
            self.data_output_path,
            self.data_cache_path,
            self.data_logs_path,
        ]:
            path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to ensure single instance.
    
    Returns:
        Settings instance
    """
    settings = Settings()
    settings.create_directories()
    return settings