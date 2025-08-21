"""
Environment validation script for Restaurant Recommendation Multi-Agent System.
Checks all required configurations and dependencies before starting the application.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


class EnvironmentValidator:
    """
    Validates environment configuration and dependencies.
    Ensures all required services and credentials are properly configured.
    """

    def __init__(self):
        """Initialize validator with configuration requirements."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.success: List[str] = []
        
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            self.success.append(f"✓ Found .env file at {env_path}")
        else:
            self.errors.append(f"✗ No .env file found. Copy .env.example to .env and configure it.")

    def check_required_vars(self) -> None:
        """Validate all required environment variables are set."""
        required_vars = {
            "OPENAI_API_KEY": "OpenAI API key for LLM and embeddings",
            "SUPABASE_URL": "Supabase project URL",
            "SUPABASE_KEY": "Supabase anonymous key",
            "SUPABASE_DB_URL": "PostgreSQL connection string",
            "LANGFUSE_PUBLIC_KEY": "Langfuse public key for observability",
            "LANGFUSE_SECRET_KEY": "Langfuse secret key for observability",
        }
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value and value != f"your_{var.lower()}_here":
                self.success.append(f"✓ {var} is configured")
            else:
                self.errors.append(f"✗ {var} is not configured - {description}")

    def check_optional_vars(self) -> None:
        """Check optional but recommended environment variables."""
        optional_vars = {
            "CREWAI_API_KEY": "CrewAI+ features",
            "SUPABASE_SERVICE_ROLE_KEY": "Admin operations",
            "REDIS_URL": "Redis caching",
        }
        
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value and value != f"your_{var.lower()}_here":
                self.success.append(f"✓ {var} is configured ({description})")
            else:
                self.warnings.append(f"⚠ {var} not configured - Optional for {description}")

    def check_python_version(self) -> None:
        """Ensure Python version meets requirements."""
        python_version = sys.version_info
        if python_version >= (3, 9):
            self.success.append(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.errors.append(f"✗ Python 3.9+ required, found {python_version.major}.{python_version.minor}")

    def check_imports(self) -> None:
        """Verify critical packages can be imported."""
        packages = [
            ("crewai", "CrewAI framework"),
            ("docling", "Document processing"),
            ("supabase", "Supabase client"),
            ("openai", "OpenAI client"),
            ("langfuse", "Observability"),
            ("vecs", "Vector operations"),
        ]
        
        for package, description in packages:
            try:
                __import__(package)
                self.success.append(f"✓ {package} installed ({description})")
            except ImportError:
                self.errors.append(f"✗ {package} not installed - Required for {description}")

    def check_data_files(self) -> None:
        """Verify data files exist in storage directory."""
        storage_path = Path(__file__).parent.parent.parent.parent.parent / "storage"
        
        expected_files = [
            ("json/restaurants.json", "Restaurant data"),
            ("csv/coupons_2025-07-31.csv", "Coupon data"),
            ("doc/allergy.docx", "Allergen guidelines"),
            ("pdf/italian.pdf", "Sample menu"),
        ]
        
        for file_path, description in expected_files:
            full_path = storage_path / file_path
            if full_path.exists():
                self.success.append(f"✓ Found {file_path} ({description})")
            else:
                self.warnings.append(f"⚠ Missing {file_path} - {description}")

    def check_connectivity(self) -> None:
        """Test connectivity to external services."""
        import httpx
        
        services = [
            ("https://api.openai.com/v1/models", "OpenAI API"),
            (os.getenv("SUPABASE_URL", ""), "Supabase"),
            (os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"), "Langfuse"),
        ]
        
        for url, service in services:
            if not url or url.startswith("your_"):
                self.warnings.append(f"⚠ Cannot test {service} - URL not configured")
                continue
                
            try:
                response = httpx.get(url, timeout=5.0)
                if response.status_code < 500:
                    self.success.append(f"✓ {service} is reachable")
                else:
                    self.warnings.append(f"⚠ {service} returned status {response.status_code}")
            except Exception as e:
                self.warnings.append(f"⚠ Cannot reach {service}: {str(e)[:50]}")

    def display_results(self) -> None:
        """Display validation results in a formatted table."""
        console.print("\n[bold cyan]🔍 Environment Validation Results[/bold cyan]\n")
        
        total_checks = len(self.success) + len(self.warnings) + len(self.errors)
        status_emoji = "✅" if not self.errors else "❌"
        status_text = "Ready to proceed!" if not self.errors else "Issues found - please fix errors"
        
        summary = Panel(
            f"{status_emoji} [bold]{status_text}[/bold]\n\n"
            f"✓ Passed: {len(self.success)}/{total_checks}\n"
            f"⚠ Warnings: {len(self.warnings)}/{total_checks}\n"
            f"✗ Errors: {len(self.errors)}/{total_checks}",
            title="Summary",
            border_style="cyan"
        )
        console.print(summary)
        
        if self.errors:
            console.print("\n[bold red]Errors (Must Fix):[/bold red]")
            for error in self.errors:
                console.print(f"  {error}")
        
        if self.warnings:
            console.print("\n[bold yellow]Warnings (Optional):[/bold yellow]")
            for warning in self.warnings:
                console.print(f"  {warning}")
        
        if self.success:
            console.print("\n[bold green]Success:[/bold green]")
            for success in self.success:
                console.print(f"  {success}")

    def run(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            bool: True if no errors found, False otherwise
        """
        console.print("[bold]Starting environment validation...[/bold]\n")
        
        self.check_python_version()
        self.check_required_vars()
        self.check_optional_vars()
        self.check_imports()
        self.check_data_files()
        self.check_connectivity()
        
        self.display_results()
        
        if self.errors:
            console.print("\n[bold red]❌ Validation failed. Please fix the errors above.[/bold red]")
            return False
        else:
            console.print("\n[bold green]✅ Validation passed! You're ready to start.[/bold green]")
            console.print("\nNext steps:")
            console.print("1. Run: python scripts/setup_database.py")
            console.print("2. Run: python scripts/ingest_data.py")
            console.print("3. Run: python main.py")
            return True


def main():
    """Main entry point for validation script."""
    validator = EnvironmentValidator()
    success = validator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()