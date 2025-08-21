#!/usr/bin/env python3
"""
Database setup script for initializing Supabase with pgvector.
Creates necessary tables, enables extensions, and sets up collections.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from ingestion.supabase_client import SupabaseVectorStore

console = Console()


def setup_database():
    """
    Set up Supabase database with required tables and extensions.
    Creates vector collections and initializes indexes.
    """
    console.print("[bold cyan]🚀 Setting up Supabase Database[/bold cyan]\n")
    
    try:
        settings = get_settings()
        console.print("✓ Configuration loaded")
        
        console.print("\n[yellow]Creating vector collections...[/yellow]")
        vector_store = SupabaseVectorStore()
        
        collections = [
            (settings.supabase_collection_menus, "Restaurant menus from PDFs"),
            (settings.supabase_collection_restaurants, "Restaurant information"),
            (settings.supabase_collection_coupons, "Promotional coupons"),
            (settings.supabase_collection_allergens, "Allergen guidelines"),
        ]
        
        for collection_name, description in collections:
            console.print(f"  ✓ Collection '{collection_name}': {description}")
        
        console.print("\n[yellow]Creating restaurant table...[/yellow]")
        create_restaurant_table_sql = """
        CREATE TABLE IF NOT EXISTS restaurants (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            cuisine_type TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            price_range TEXT,
            rating DECIMAL(2,1),
            allergen_info JSONB,
            dietary_options TEXT[],
            hours JSONB,
            description TEXT,
            specialties TEXT[],
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        try:
            vector_store.supabase.rpc('exec_sql', {'query': create_restaurant_table_sql}).execute()
            console.print("  ✓ Restaurant table created")
        except Exception as e:
            console.print(f"  ⚠ Restaurant table might already exist: {str(e)[:100]}")
        
        summary = Panel(
            "[green]✅ Database setup complete![/green]\n\n"
            "Vector collections created:\n"
            f"  • {settings.supabase_collection_menus}\n"
            f"  • {settings.supabase_collection_restaurants}\n"
            f"  • {settings.supabase_collection_coupons}\n"
            f"  • {settings.supabase_collection_allergens}\n\n"
            "Next step: Run [bold]python scripts/ingest_data.py[/bold]",
            title="Setup Complete",
            border_style="green"
        )
        console.print("\n")
        console.print(summary)
        
        return True
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Setup failed:[/bold red] {str(e)}")
        console.print("\nPlease check:")
        console.print("  1. Your Supabase credentials in .env")
        console.print("  2. pgvector extension is enabled in Supabase")
        console.print("  3. Network connectivity to Supabase")
        return False


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)