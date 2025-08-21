"""
Pydantic models for data validation and serialization.
Defines the structure of documents, restaurants, coupons, and allergen information.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    """Enumeration of supported document types."""

    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    DOCX = "docx"
    MARKDOWN = "markdown"


class CuisineType(str, Enum):
    """Enumeration of cuisine types."""

    AMERICAN = "american"
    CHINESE = "chinese"
    FRENCH = "french"
    INDIAN = "indian"
    ITALIAN = "italian"
    JAPANESE = "japanese"
    MEXICAN = "mexican"
    THAI = "thai"


class AllergenType(str, Enum):
    """Common allergen types."""

    NUTS = "nuts"
    DAIRY = "dairy"
    EGGS = "eggs"
    GLUTEN = "gluten"
    SHELLFISH = "shellfish"
    SOY = "soy"
    FISH = "fish"
    SESAME = "sesame"
    SULFITES = "sulfites"
    MUSTARD = "mustard"


class DocumentMetadata(BaseModel):
    """
    Metadata associated with a document.
    Stores source information and processing details.
    """

    source: str = Field(..., description="Source file path or URL")
    doc_type: DocumentType = Field(..., description="Type of document")
    cuisine_type: Optional[CuisineType] = Field(default=None, description="Cuisine type if applicable")
    page_number: Optional[int] = Field(default=None, description="Page number if applicable")
    total_pages: Optional[int] = Field(default=None, description="Total pages in document")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    language: str = Field(default="en", description="Document language")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentChunk(BaseModel):
    """
    Represents a chunk of text from a document.
    Used for vector storage and retrieval.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique chunk identifier")
    document_id: UUID = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk text content")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    metadata: DocumentMetadata = Field(..., description="Chunk metadata")
    chunk_index: int = Field(..., description="Position in document")
    token_count: int = Field(..., description="Number of tokens")
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """
        Validate content is not empty.
        
        Args:
            v: Content string
            
        Returns:
            Validated content
            
        Raises:
            ValueError: If content is empty
        """
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


class Document(BaseModel):
    """
    Represents a complete document.
    Contains all chunks and metadata for a processed document.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full document content")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="Document chunks")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def add_chunk(self, chunk: DocumentChunk) -> None:
        """
        Add a chunk to the document.
        
        Args:
            chunk: DocumentChunk to add
        """
        chunk.document_id = self.id
        self.chunks.append(chunk)
        self.updated_at = datetime.utcnow()


class Restaurant(BaseModel):
    """
    Restaurant information model.
    Contains details about a restaurant including allergen information.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique restaurant identifier")
    name: str = Field(..., description="Restaurant name")
    cuisine_type: CuisineType = Field(..., description="Type of cuisine")
    address: str = Field(..., description="Restaurant address")
    phone: str = Field(..., description="Contact phone number")
    email: Optional[str] = Field(default=None, description="Contact email")
    website: Optional[str] = Field(default=None, description="Restaurant website")
    price_range: str = Field(..., description="Price range (e.g., $, $$, $$$)")
    rating: float = Field(..., ge=0, le=5, description="Restaurant rating")
    allergen_info: Dict[str, List[str]] = Field(
        default_factory=dict, description="Allergen information by dish"
    )
    dietary_options: List[str] = Field(
        default_factory=list, description="Available dietary options"
    )
    hours: Dict[str, str] = Field(default_factory=dict, description="Operating hours")
    description: str = Field(..., description="Restaurant description")
    specialties: List[str] = Field(default_factory=list, description="Restaurant specialties")
    
    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: float) -> float:
        """
        Validate rating is within range.
        
        Args:
            v: Rating value
            
        Returns:
            Validated rating
            
        Raises:
            ValueError: If rating is out of range
        """
        if not 0 <= v <= 5:
            raise ValueError("Rating must be between 0 and 5")
        return round(v, 1)
    
    @field_validator("price_range")
    @classmethod
    def validate_price_range(cls, v: str) -> str:
        """
        Validate price range format.
        
        Args:
            v: Price range string
            
        Returns:
            Validated price range
            
        Raises:
            ValueError: If price range is invalid
        """
        valid_ranges = {"$", "$$", "$$$", "$$$$"}
        if v not in valid_ranges:
            raise ValueError(f"Price range must be one of {valid_ranges}")
        return v


class Coupon(BaseModel):
    """
    Promotional coupon model.
    Contains discount information and validity periods.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique coupon identifier")
    restaurant_id: UUID = Field(..., description="Associated restaurant ID")
    restaurant_name: str = Field(..., description="Restaurant name")
    code: str = Field(..., description="Coupon code")
    description: str = Field(..., description="Coupon description")
    discount_percentage: Optional[float] = Field(
        default=None, ge=0, le=100, description="Discount percentage"
    )
    discount_amount: Optional[float] = Field(
        default=None, ge=0, description="Fixed discount amount"
    )
    minimum_order: Optional[float] = Field(
        default=None, ge=0, description="Minimum order amount"
    )
    valid_from: datetime = Field(..., description="Validity start date")
    valid_until: datetime = Field(..., description="Validity end date")
    terms_conditions: str = Field(..., description="Terms and conditions")
    max_uses: Optional[int] = Field(default=None, ge=1, description="Maximum uses")
    applicable_items: List[str] = Field(
        default_factory=list, description="Items coupon applies to"
    )
    
    @field_validator("valid_until")
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        """
        Validate end date is after start date.
        
        Args:
            v: End date
            info: Field validation info
            
        Returns:
            Validated end date
            
        Raises:
            ValueError: If end date is before start date
        """
        if "valid_from" in info.data and v <= info.data["valid_from"]:
            raise ValueError("valid_until must be after valid_from")
        return v
    
    def is_valid(self) -> bool:
        """
        Check if coupon is currently valid.
        
        Returns:
            True if coupon is valid, False otherwise
        """
        now = datetime.utcnow()
        return self.valid_from <= now <= self.valid_until


class AllergenInfo(BaseModel):
    """
    Allergen information and guidelines.
    Contains detailed allergen data and safety information.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique allergen info identifier")
    allergen_type: AllergenType = Field(..., description="Type of allergen")
    common_names: List[str] = Field(..., description="Common names for allergen")
    description: str = Field(..., description="Allergen description")
    severity_level: str = Field(..., description="Typical severity level")
    symptoms: List[str] = Field(..., description="Common symptoms")
    hidden_sources: List[str] = Field(
        default_factory=list, description="Hidden sources of allergen"
    )
    cross_contamination_risks: List[str] = Field(
        default_factory=list, description="Cross-contamination risks"
    )
    safe_alternatives: List[str] = Field(
        default_factory=list, description="Safe alternatives"
    )
    regulatory_info: Dict[str, str] = Field(
        default_factory=dict, description="Regulatory information by region"
    )
    
    @field_validator("severity_level")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """
        Validate severity level.
        
        Args:
            v: Severity level string
            
        Returns:
            Validated severity level
            
        Raises:
            ValueError: If severity level is invalid
        """
        valid_levels = {"mild", "moderate", "severe", "life-threatening"}
        v_lower = v.lower()
        if v_lower not in valid_levels:
            raise ValueError(f"Severity level must be one of {valid_levels}")
        return v_lower