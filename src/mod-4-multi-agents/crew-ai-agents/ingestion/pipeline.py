"""
Complete ingestion pipeline orchestrating document processing, embedding generation, and storage.
Provides batch processing, progress tracking, and error handling.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from config import get_settings
from database.models import (
    AllergenInfo, AllergenType, Coupon, CuisineType, 
    Document, Restaurant
)
from .docling_processor import DoclingProcessor
from .embeddings import EmbeddingGenerator
from .supabase_client import SupabaseVectorStore


console = Console()


class IngestionPipeline:
    """
    Orchestrates the complete document ingestion pipeline.
    Processes documents, generates embeddings, and stores in Supabase.
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.settings = get_settings()
        self.processor = DoclingProcessor()
        self.embedder = EmbeddingGenerator()
        self.vector_store = SupabaseVectorStore()
        
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "processing_time": 0.0,
            "errors": []
        }

    def run_full_ingestion(self) -> Dict[str, any]:
        """
        Run complete ingestion for all data sources.
        
        Returns:
            Dictionary with ingestion statistics
        """
        console.print("[bold cyan]Starting Full Ingestion Pipeline[/bold cyan]\n")
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            tasks = []
            
            task = progress.add_task("[yellow]Processing menu PDFs...", total=8)
            tasks.append(task)
            self._process_menus(progress, task)
            
            task = progress.add_task("[yellow]Processing restaurant data...", total=1)
            tasks.append(task)
            self._process_restaurants(progress, task)
            
            task = progress.add_task("[yellow]Processing coupon data...", total=1)
            tasks.append(task)
            self._process_coupons(progress, task)
            
            task = progress.add_task("[yellow]Processing allergen guidelines...", total=1)
            tasks.append(task)
            self._process_allergens(progress, task)
            
            task = progress.add_task("[yellow]Creating vector indexes...", total=4)
            tasks.append(task)
            self._create_indexes(progress, task)
        
        end_time = datetime.now()
        self.stats["processing_time"] = (end_time - start_time).total_seconds()
        
        self._display_summary()
        
        return self.stats

    def _process_menus(self, progress: Progress, task_id: int) -> None:
        """
        Process restaurant menu PDFs.
        
        Args:
            progress: Progress bar instance
            task_id: Task ID for progress tracking
        """
        pdf_dir = self.settings.get_absolute_storage_path() / "pdf"
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            try:
                document = self.processor.process_file(pdf_file)
                
                document = self.embedder.process_document(document)
                
                chunk_ids = self.vector_store.upsert_document_chunks(
                    document.chunks,
                    self.settings.supabase_collection_menus
                )
                
                self.stats["total_documents"] += 1
                self.stats["total_chunks"] += len(document.chunks)
                self.stats["total_tokens"] += sum(c.token_count for c in document.chunks)
                self.stats["estimated_cost"] += self.embedder.estimate_cost(document.content)
                
                progress.update(task_id, advance=1)
                console.print(f"  ✓ {pdf_file.name}: {len(document.chunks)} chunks")
                
            except Exception as e:
                self.stats["errors"].append(f"Menu {pdf_file.name}: {str(e)}")
                console.print(f"  ✗ {pdf_file.name}: [red]{str(e)}[/red]")
                progress.update(task_id, advance=1)

    def _process_restaurants(self, progress: Progress, task_id: int) -> None:
        """
        Process restaurant JSON data.
        
        Args:
            progress: Progress bar instance
            task_id: Task ID for progress tracking
        """
        json_file = self.settings.get_absolute_storage_path() / "json" / "restaurants.json"
        
        try:
            with open(json_file, 'r') as f:
                restaurants_data = json.load(f)
            
            for rest_data in restaurants_data:
                restaurant = self._create_restaurant_from_json(rest_data)
                
                description = f"{restaurant.name} - {restaurant.description}. Specialties: {', '.join(restaurant.specialties)}"
                embedding = self.embedder.generate_embedding(description)
                
                self.vector_store.store_restaurant(restaurant, embedding)
                
                self.stats["total_documents"] += 1
                self.stats["estimated_cost"] += self.embedder.estimate_cost(description)
            
            progress.update(task_id, advance=1)
            console.print(f"  ✓ restaurants.json: {len(restaurants_data)} restaurants")
            
        except Exception as e:
            self.stats["errors"].append(f"Restaurants: {str(e)}")
            console.print(f"  ✗ restaurants.json: [red]{str(e)}[/red]")
            progress.update(task_id, advance=1)

    def _process_coupons(self, progress: Progress, task_id: int) -> None:
        """
        Process coupon CSV data.
        
        Args:
            progress: Progress bar instance
            task_id: Task ID for progress tracking
        """
        csv_file = self.settings.get_absolute_storage_path() / "csv" / "coupons_2025-07-31.csv"
        
        try:
            df = pd.read_csv(csv_file)
            
            for _, row in df.iterrows():
                coupon = self._create_coupon_from_csv(row)
                
                description = f"{coupon.restaurant_name}: {coupon.description}. Code: {coupon.code}"
                embedding = self.embedder.generate_embedding(description)
                
                self.vector_store.store_coupon(coupon, embedding)
                
                self.stats["estimated_cost"] += self.embedder.estimate_cost(description)
            
            self.stats["total_documents"] += len(df)
            
            progress.update(task_id, advance=1)
            console.print(f"  ✓ coupons.csv: {len(df)} coupons")
            
        except Exception as e:
            self.stats["errors"].append(f"Coupons: {str(e)}")
            console.print(f"  ✗ coupons.csv: [red]{str(e)}[/red]")
            progress.update(task_id, advance=1)

    def _process_allergens(self, progress: Progress, task_id: int) -> None:
        """
        Process allergen guidelines DOCX.
        
        Args:
            progress: Progress bar instance
            task_id: Task ID for progress tracking
        """
        docx_file = self.settings.get_absolute_storage_path() / "doc" / "allergy.docx"
        
        try:
            document = self.processor.process_file(docx_file)
            
            document = self.embedder.process_document(document)
            
            chunk_ids = self.vector_store.upsert_document_chunks(
                document.chunks,
                self.settings.supabase_collection_allergens
            )
            
            self._create_allergen_info_objects()
            
            self.stats["total_documents"] += 1
            self.stats["total_chunks"] += len(document.chunks)
            self.stats["total_tokens"] += sum(c.token_count for c in document.chunks)
            self.stats["estimated_cost"] += self.embedder.estimate_cost(document.content)
            
            progress.update(task_id, advance=1)
            console.print(f"  ✓ allergy.docx: {len(document.chunks)} chunks")
            
        except Exception as e:
            self.stats["errors"].append(f"Allergens: {str(e)}")
            console.print(f"  ✗ allergy.docx: [red]{str(e)}[/red]")
            progress.update(task_id, advance=1)

    def _create_indexes(self, progress: Progress, task_id: int) -> None:
        """
        Create vector indexes for all collections.
        
        Args:
            progress: Progress bar instance
            task_id: Task ID for progress tracking
        """
        collections = [
            self.settings.supabase_collection_menus,
            self.settings.supabase_collection_restaurants,
            self.settings.supabase_collection_coupons,
            self.settings.supabase_collection_allergens
        ]
        
        for collection in collections:
            try:
                self.vector_store.create_index(collection, index_type="ivfflat")
                progress.update(task_id, advance=1)
                console.print(f"  ✓ Index created for {collection}")
            except Exception as e:
                console.print(f"  ⚠ Index for {collection}: {str(e)}")
                progress.update(task_id, advance=1)

    def _create_restaurant_from_json(self, data: Dict) -> Restaurant:
        """
        Create Restaurant object from JSON data.
        
        Args:
            data: Restaurant data dictionary
            
        Returns:
            Restaurant object
        """
        cuisine_map = {
            "american": CuisineType.AMERICAN,
            "chinese": CuisineType.CHINESE,
            "french": CuisineType.FRENCH,
            "indian": CuisineType.INDIAN,
            "italian": CuisineType.ITALIAN,
            "japanese": CuisineType.JAPANESE,
            "mexican": CuisineType.MEXICAN,
            "thai": CuisineType.THAI
        }
        
        cuisine = cuisine_map.get(
            data.get("cuisine_type", "").lower(),
            CuisineType.AMERICAN
        )
        
        return Restaurant(
            name=data.get("name", "Unknown"),
            cuisine_type=cuisine,
            address=data.get("address", ""),
            phone=data.get("phone", ""),
            email=data.get("email"),
            website=data.get("website"),
            price_range=data.get("price_range", "$$"),
            rating=float(data.get("rating", 4.0)),
            allergen_info=data.get("allergen_info", {}),
            dietary_options=data.get("dietary_options", []),
            hours=data.get("hours", {}),
            description=data.get("description", ""),
            specialties=data.get("specialties", [])
        )

    def _create_coupon_from_csv(self, row: pd.Series) -> Coupon:
        """
        Create Coupon object from CSV row.
        
        Args:
            row: Pandas Series with coupon data
            
        Returns:
            Coupon object
        """
        from uuid import uuid4
        
        return Coupon(
            restaurant_id=uuid4(),
            restaurant_name=row.get("restaurant_name", "Unknown"),
            code=row.get("code", ""),
            description=row.get("description", ""),
            discount_percentage=float(row.get("discount_percentage", 0)) if pd.notna(row.get("discount_percentage")) else None,
            discount_amount=float(row.get("discount_amount", 0)) if pd.notna(row.get("discount_amount")) else None,
            minimum_order=float(row.get("minimum_order", 0)) if pd.notna(row.get("minimum_order")) else None,
            valid_from=pd.to_datetime(row.get("valid_from", datetime.now())),
            valid_until=pd.to_datetime(row.get("valid_until", datetime.now())),
            terms_conditions=row.get("terms_conditions", ""),
            max_uses=int(row.get("max_uses")) if pd.notna(row.get("max_uses")) else None,
            applicable_items=row.get("applicable_items", "").split(",") if row.get("applicable_items") else []
        )

    def _create_allergen_info_objects(self) -> None:
        """Create standard allergen information objects."""
        allergen_data = [
            {
                "type": AllergenType.NUTS,
                "names": ["peanuts", "tree nuts", "almonds", "cashews", "walnuts"],
                "description": "Nuts and nut products can cause severe allergic reactions",
                "severity": "life-threatening",
                "symptoms": ["hives", "swelling", "difficulty breathing", "anaphylaxis"]
            },
            {
                "type": AllergenType.DAIRY,
                "names": ["milk", "cheese", "butter", "cream", "yogurt"],
                "description": "Dairy products contain lactose and milk proteins",
                "severity": "moderate",
                "symptoms": ["digestive issues", "skin reactions", "respiratory problems"]
            },
            {
                "type": AllergenType.GLUTEN,
                "names": ["wheat", "barley", "rye", "spelt"],
                "description": "Gluten is found in many grain products",
                "severity": "severe",
                "symptoms": ["digestive damage", "nutrient malabsorption", "fatigue"]
            }
        ]
        
        for allergen in allergen_data:
            info = AllergenInfo(
                allergen_type=allergen["type"],
                common_names=allergen["names"],
                description=allergen["description"],
                severity_level=allergen["severity"],
                symptoms=allergen["symptoms"],
                hidden_sources=[],
                cross_contamination_risks=[],
                safe_alternatives=[]
            )
            
            description = f"{info.allergen_type.value}: {info.description}"
            embedding = self.embedder.generate_embedding(description)
            
            self.vector_store.store_allergen_info(info, embedding)

    def _display_summary(self) -> None:
        """Display ingestion summary statistics."""
        table = Table(title="Ingestion Pipeline Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Documents", str(self.stats["total_documents"]))
        table.add_row("Total Chunks", str(self.stats["total_chunks"]))
        table.add_row("Total Tokens", f"{self.stats['total_tokens']:,}")
        table.add_row("Estimated Cost", f"${self.stats['estimated_cost']:.4f}")
        table.add_row("Processing Time", f"{self.stats['processing_time']:.2f} seconds")
        table.add_row("Errors", str(len(self.stats["errors"])))
        
        console.print("\n")
        console.print(table)
        
        if self.stats["errors"]:
            console.print("\n[bold red]Errors encountered:[/bold red]")
            for error in self.stats["errors"]:
                console.print(f"  • {error}")

    def validate_ingestion(self) -> bool:
        """
        Validate that ingestion was successful.
        
        Returns:
            True if validation passes
        """
        console.print("\n[bold cyan]Validating Ingestion...[/bold cyan]")
        
        collections = [
            (self.settings.supabase_collection_menus, "Menus"),
            (self.settings.supabase_collection_restaurants, "Restaurants"),
            (self.settings.supabase_collection_coupons, "Coupons"),
            (self.settings.supabase_collection_allergens, "Allergens")
        ]
        
        all_valid = True
        for collection_name, display_name in collections:
            stats = self.vector_store.get_collection_stats(collection_name)
            if stats["count"] > 0:
                console.print(f"  ✓ {display_name}: {stats['count']} vectors")
            else:
                console.print(f"  ✗ {display_name}: No data found")
                all_valid = False
        
        return all_valid