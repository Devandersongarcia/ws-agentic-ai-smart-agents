"""
Data ingestion script for processing and storing all restaurant data.
Processes PDFs, JSON, CSV, and DOCX files and stores them in Supabase.
"""

import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from ingestion import IngestionPipeline

console = Console()


def ingest_data():
    """
    Run the complete data ingestion pipeline.
    Processes all files from the storage directory.
    """
    console.print("[bold cyan]📚 Starting Data Ingestion Pipeline[/bold cyan]\n")
    
    try:
        console.print("Initializing ingestion pipeline...")
        pipeline = IngestionPipeline()
        console.print("✓ Pipeline initialized\n")
        
        settings = get_settings()
        storage_path = settings.get_absolute_storage_path()
        
        console.print("[bold]Data sources found:[/bold]")
        console.print(f"  📁 Storage directory: {storage_path}")
        
        pdf_files = list((storage_path / "pdf").glob("*.pdf"))
        json_files = list((storage_path / "json").glob("*.json"))
        csv_files = list((storage_path / "csv").glob("*.csv"))
        docx_files = list((storage_path / "doc").glob("*.docx"))
        
        console.print(f"  📄 PDF files: {len(pdf_files)} menus")
        console.print(f"  📊 JSON files: {len(json_files)} restaurant data")
        console.print(f"  📈 CSV files: {len(csv_files)} coupon data")
        console.print(f"  📝 DOCX files: {len(docx_files)} allergen guidelines")
        
        total_files = len(pdf_files) + len(json_files) + len(csv_files) + len(docx_files)
        
        if total_files == 0:
            console.print("\n[bold red]No files found to process![/bold red]")
            console.print(f"Please check that files exist in: {storage_path}")
            return False
        
        console.print(f"\n[yellow]Ready to process {total_files} files[/yellow]")
        console.print("This will:")
        console.print("  • Extract content using Docling")
        console.print("  • Generate embeddings with OpenAI")
        console.print("  • Store vectors in Supabase")
        console.print("  • Create search indexes")
        
        response = console.input("\n[bold]Proceed with ingestion? (y/n):[/bold] ")
        if response.lower() != 'y':
            console.print("Ingestion cancelled.")
            return False
        
        console.print("\n" + "="*50 + "\n")
        
        start_time = datetime.now()
        stats = pipeline.run_full_ingestion()
        
        console.print("\n" + "="*50)
        validation_passed = pipeline.validate_ingestion()
        
        elapsed_time = datetime.now() - start_time
        
        if validation_passed and len(stats.get("errors", [])) == 0:
            summary = Panel(
                "[green]✅ Ingestion completed successfully![/green]\n\n"
                f"📊 Statistics:\n"
                f"  • Documents processed: {stats['total_documents']}\n"
                f"  • Chunks created: {stats['total_chunks']}\n"
                f"  • Tokens processed: {stats['total_tokens']:,}\n"
                f"  • Estimated cost: ${stats['estimated_cost']:.4f}\n"
                f"  • Total time: {elapsed_time.total_seconds():.2f} seconds\n\n"
                "Next step: Run [bold]python main.py[/bold] to start the agents",
                title="Ingestion Complete",
                border_style="green"
            )
        else:
            error_count = len(stats.get("errors", []))
            summary = Panel(
                "[yellow]⚠ Ingestion completed with warnings[/yellow]\n\n"
                f"📊 Statistics:\n"
                f"  • Documents processed: {stats['total_documents']}\n"
                f"  • Chunks created: {stats['total_chunks']}\n"
                f"  • Errors encountered: {error_count}\n"
                f"  • Total time: {elapsed_time.total_seconds():.2f} seconds\n\n"
                "Check the errors above and consider re-running for failed files",
                title="Ingestion Completed with Issues",
                border_style="yellow"
            )
        
        console.print("\n")
        console.print(summary)
        
        return validation_passed
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Ingestion interrupted by user[/yellow]")
        return False
    except Exception as e:
        console.print(f"\n[bold red]❌ Ingestion failed:[/bold red] {str(e)}")
        console.print("\nPlease check:")
        console.print("  1. All environment variables are set correctly")
        console.print("  2. OpenAI API key is valid")
        console.print("  3. Supabase is accessible")
        console.print("  4. Data files exist in the storage directory")
        
        import traceback
        console.print("\n[dim]Stack trace:[/dim]")
        console.print(traceback.format_exc())
        
        return False


if __name__ == "__main__":
    success = ingest_data()
    sys.exit(0 if success else 1)