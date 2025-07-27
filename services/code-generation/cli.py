"""
SchemaSage CLI Tool
Command-line interface for schema generation, data analysis, and cleaning
"""
import click
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
import requests

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.nl_schema_converter import NLSchemaConverter
from core.code_generator import CodeGenerator
from core.data_quality_analyzer import DataQualityAnalyzer
from core.data_cleaning_service import DataCleaningService
from core.erd_generator import ERDGenerator
from core.api_scaffold_generator import APIScaffoldGenerator
from core.ai_schema_critic import AISchemacritic
from core.schema_merger import SchemaMerger
from core.schema_version_control import SchemaVersionControl
from core.performance_monitor import performance_monitor, PerformanceProfiler
from models.schemas import SchemaResponse

console = Console()

class SchemaSageCLI:
    """Main CLI application class"""
    
    def __init__(self):
        self.nl_converter = NLSchemaConverter()
        self.code_generator = CodeGenerator()
        self.data_analyzer = DataQualityAnalyzer()
        self.data_cleaner = DataCleaningService()
        self.erd_generator = ERDGenerator()
        self.api_generator = APIScaffoldGenerator()
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load CLI configuration"""
        config_path = Path.home() / ".schemasage" / "config.json"
        
        default_config = {
            "default_output_format": "sqlalchemy",
            "default_output_dir": "./output",
            "ai_service_url": "http://localhost:8000",
            "auto_clean_suggestions": True,
            "verbose": False
        }
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    return {**default_config, **config}
            except:
                pass
        
        return default_config
    
    def _save_config(self):
        """Save CLI configuration"""
        config_path = Path.home() / ".schemasage" / "config.json"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config-file', type=click.Path(), help='Path to config file')
@click.pass_context
def cli(ctx, verbose, config_file):
    """SchemaSage - AI-powered schema generation and data analysis tool"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['cli'] = SchemaSageCLI()
    
    if verbose:
        console.print("[bold blue]SchemaSage CLI - Verbose mode enabled[/bold blue]")

@cli.command()
@click.argument('description', required=True)
@click.option('--format', '-f', 
              type=click.Choice(['sqlalchemy', 'sql', 'prisma', 'typeorm', 'django', 'typescript', 'json']),
              default='sqlalchemy',
              help='Output format for generated code')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode for refining schema')
@click.pass_context
def generate(ctx, description, format, output, interactive):
    """Generate schema and code from natural language description"""
    cli_instance = ctx.obj['cli']
    verbose = ctx.obj['verbose']
    
    async def run_generation():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Step 1: Convert description to schema
            task1 = progress.add_task("Converting description to schema...", total=None)
            
            try:
                schema = await cli_instance.nl_converter.convert_natural_language_to_schema(description)
                progress.update(task1, description="✅ Schema generated successfully")
                
                if verbose:
                    console.print(f"\n[bold green]Generated Schema:[/bold green]")
                    console.print(f"  📊 Tables: {len(schema.tables)}")
                    console.print(f"  🔗 Relationships: {len(schema.relationships)}")
                
                # Interactive refinement
                if interactive:
                    schema = await _interactive_schema_refinement(schema)
                
                # Step 2: Generate code
                task2 = progress.add_task(f"Generating {format} code...", total=None)
                
                generated_code = await cli_instance.code_generator.generate_code(
                    schema=schema,
                    format=format,
                    options={}
                )
                
                progress.update(task2, description=f"✅ {format} code generated")
                
                # Output handling
                if output:
                    output_path = Path(output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, 'w') as f:
                        f.write(generated_code)
                    
                    console.print(f"\n[bold green]✅ Code saved to: {output_path}[/bold green]")
                else:
                    console.print(f"\n[bold green]Generated {format.upper()} Code:[/bold green]")
                    syntax = Syntax(generated_code, _get_syntax_lexer(format), theme="monokai")
                    console.print(Panel(syntax, title=f"{format.upper()} Output"))
                
            except Exception as e:
                progress.update(task1, description=f"❌ Error: {str(e)}")
                console.print(f"[bold red]Error: {str(e)}[/bold red]")
                raise click.Abort()
    
    asyncio.run(run_generation())

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output-format', '-f', 
              type=click.Choice(['json', 'table', 'html']),
              default='table',
              help='Output format for quality report')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--auto-clean', is_flag=True, help='Automatically apply suggested cleaning')
@click.pass_context
def analyze(ctx, file_path, output_format, output, auto_clean):
    """Analyze data quality of a file"""
    cli_instance = ctx.obj['cli']
    verbose = ctx.obj['verbose']
    
    async def run_analysis():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Analyzing data quality...", total=None)
            
            try:
                # Determine file type
                file_ext = Path(file_path).suffix.lower()
                file_type_map = {'.csv': 'csv', '.xlsx': 'xlsx', '.xls': 'xls', '.json': 'json'}
                file_type = file_type_map.get(file_ext, 'csv')
                
                # Read and analyze file
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                report = await cli_instance.data_cleaner.analyze_file_quality(
                    file_content, file_type
                )
                
                progress.update(task, description="✅ Analysis complete")
                
                # Display results
                _display_quality_report(report, output_format, verbose)
                
                # Auto-cleaning option
                if auto_clean and report.recommendations:
                    console.print("\n[bold yellow]🧹 Auto-cleaning enabled[/bold yellow]")
                    await _auto_apply_cleaning(cli_instance, file_content, file_type, report, file_path)
                elif report.recommendations:
                    if Confirm.ask("\n🤔 Would you like to apply cleaning recommendations?"):
                        await _interactive_cleaning(cli_instance, file_content, file_type, report, file_path)
                
                # Save report if output specified
                if output:
                    _save_quality_report(report, output, output_format)
                    console.print(f"\n[bold green]📊 Report saved to: {output}[/bold green]")
                
            except Exception as e:
                progress.update(task, description=f"❌ Error: {str(e)}")
                console.print(f"[bold red]Error analyzing file: {str(e)}[/bold red]")
                raise click.Abort()
    
    asyncio.run(run_analysis())

@cli.command()
@click.argument('description', required=True)
@click.option('--layout', '-l', 
              type=click.Choice(['force_directed', 'hierarchical', 'circular', 'grid']),
              default='force_directed',
              help='ERD layout algorithm')
@click.option('--format', '-f',
              type=click.Choice(['json', 'svg', 'html']),
              default='json',
              help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def erd(ctx, description, layout, format, output):
    """Generate Entity Relationship Diagram from description"""
    cli_instance = ctx.obj['cli']
    verbose = ctx.obj['verbose']
    
    async def run_erd_generation():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task1 = progress.add_task("Generating schema...", total=None)
            
            try:
                # Generate schema
                schema = await cli_instance.nl_converter.convert_natural_language_to_schema(description)
                progress.update(task1, description="✅ Schema generated")
                
                # Generate ERD
                task2 = progress.add_task(f"Creating {layout} ERD...", total=None)
                
                erd_data = cli_instance.erd_generator.generate_erd_data(
                    schema=schema,
                    layout_algorithm=layout
                )
                
                progress.update(task2, description="✅ ERD generated")
                
                # Export ERD
                exported_erd = cli_instance.erd_generator.export_erd(erd_data, format)
                
                if output:
                    output_path = Path(output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, 'w') as f:
                        f.write(exported_erd)
                    
                    console.print(f"\n[bold green]📊 ERD saved to: {output_path}[/bold green]")
                else:
                    console.print(f"\n[bold green]Generated ERD ({layout} layout):[/bold green]")
                    
                    if format == 'json':
                        syntax = Syntax(exported_erd, "json", theme="monokai")
                        console.print(Panel(syntax, title="ERD Data"))
                    else:
                        console.print(exported_erd)
                
                # Display ERD statistics
                metadata = erd_data['metadata']
                console.print(f"\n[bold blue]📈 ERD Statistics:[/bold blue]")
                console.print(f"  🏢 Tables: {metadata['table_count']}")
                console.print(f"  🔗 Relationships: {metadata['relationship_count']}")
                console.print(f"  📐 Canvas: {metadata['canvas_bounds']['width']}x{metadata['canvas_bounds']['height']}")
                console.print(f"  🎨 Layout: {layout}")
                
            except Exception as e:
                progress.update(task1, description=f"❌ Error: {str(e)}")
                console.print(f"[bold red]Error generating ERD: {str(e)}[/bold red]")
                raise click.Abort()
    
    asyncio.run(run_erd_generation())

@cli.command()
@click.argument('description', required=True)
@click.option('--framework', '-f',
              type=click.Choice(['fastapi', 'express', 'nestjs', 'spring_boot', 'rails', 'django_rest', 'asp_net_core']),
              default='fastapi',
              help='API framework')
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory for generated files')
@click.option('--include-tests', is_flag=True, default=True, help='Include test files')
@click.pass_context
def scaffold(ctx, description, framework, output_dir, include_tests):
    """Generate complete API scaffolding from description"""
    cli_instance = ctx.obj['cli']
    verbose = ctx.obj['verbose']
    
    async def run_scaffolding():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task1 = progress.add_task("Generating schema...", total=None)
            
            try:
                # Generate schema
                schema = await cli_instance.nl_converter.convert_natural_language_to_schema(description)
                progress.update(task1, description="✅ Schema generated")
                
                # Generate API scaffold
                task2 = progress.add_task(f"Creating {framework} scaffold...", total=None)
                
                scaffold_options = {"include_tests": include_tests}
                scaffold_data = cli_instance.api_generator.generate_api_scaffold(
                    schema=schema,
                    framework=framework,
                    options=scaffold_options
                )
                
                progress.update(task2, description="✅ Scaffold generated")
                
                # Save files
                if output_dir:
                    output_path = Path(output_dir)
                    _save_scaffold_files(scaffold_data, output_path, verbose)
                    console.print(f"\n[bold green]🚀 API scaffold saved to: {output_path}[/bold green]")
                else:
                    _display_scaffold_preview(scaffold_data, verbose)
                
                # Display scaffold statistics
                metadata = scaffold_data['metadata']
                console.print(f"\n[bold blue]📊 Scaffold Statistics:[/bold blue]")
                console.print(f"  🏗️  Framework: {framework}")
                console.print(f"  📋 Components: {len(scaffold_data['components'])}")
                console.print(f"  🌐 Endpoints: {metadata['endpoint_count']}")
                console.print(f"  📁 Generated Files: {metadata.get('generated_files', 'N/A')}")
                
            except Exception as e:
                progress.update(task1, description=f"❌ Error: {str(e)}")
                console.print(f"[bold red]Error generating scaffold: {str(e)}[/bold red]")
                raise click.Abort()
    
    asyncio.run(run_scaffolding())

@cli.command()
@click.option('--service-url', default='http://localhost:8000', help='SchemaSage service URL')
@click.pass_context
def serve(ctx, service_url):
    """Start SchemaSage development server"""
    console.print(f"[bold blue]🚀 Starting SchemaSage development server...[/bold blue]")
    console.print(f"   Service URL: {service_url}")
    
    try:
        # This would start the FastAPI server
        import uvicorn
        from main import app
        
        console.print("[bold green]✅ Server starting on http://localhost:8000[/bold green]")
        console.print("   📚 API Documentation: http://localhost:8000/docs")
        console.print("   🔍 Health Check: http://localhost:8000/health")
        console.print("\n[dim]Press Ctrl+C to stop[/dim]")
        
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
        
    except ImportError:
        console.print("[bold red]❌ Server dependencies not found. Run from service directory.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Error starting server: {str(e)}[/bold red]")

@cli.command()
@click.pass_context
def config(ctx):
    """Configure SchemaSage CLI settings"""
    cli_instance = ctx.obj['cli']
    
    console.print("[bold blue]⚙️  SchemaSage Configuration[/bold blue]")
    
    # Display current configuration
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")
    
    for key, value in cli_instance.config.items():
        table.add_row(key, str(value))
    
    console.print(table)
    
    # Allow configuration changes
    if Confirm.ask("\n🔧 Would you like to modify settings?"):
        for key, current_value in cli_instance.config.items():
            new_value = Prompt.ask(
                f"[cyan]{key}[/cyan]",
                default=str(current_value)
            )
            
            # Type conversion
            if isinstance(current_value, bool):
                cli_instance.config[key] = new_value.lower() in ['true', 'yes', '1']
            elif isinstance(current_value, int):
                cli_instance.config[key] = int(new_value)
            else:
                cli_instance.config[key] = new_value
        
        cli_instance._save_config()
        console.print("[bold green]✅ Configuration saved[/bold green]")

@cli.command()
def version():
    """Show SchemaSage version information"""
    console.print(Panel.fit(
        "[bold blue]SchemaSage CLI v1.0.0[/bold blue]\n"
        "AI-powered schema generation and data analysis\n\n"
        "[dim]• Schema generation from natural language[/dim]\n"
        "[dim]• Multi-format code generation[/dim]\n"
        "[dim]• Data quality analysis and cleaning[/dim]\n"
        "[dim]• ERD generation and visualization[/dim]\n"
        "[dim]• API scaffolding for multiple frameworks[/dim]",
        title="🔮 SchemaSage"
    ))

# Helper functions

async def _interactive_schema_refinement(schema):
    """Interactive schema refinement"""
    console.print("\n[bold yellow]🔧 Interactive Schema Refinement[/bold yellow]")
    
    # Display schema summary
    table = Table(title="Generated Schema")
    table.add_column("Table", style="cyan")
    table.add_column("Columns", style="magenta")
    table.add_column("Relationships", style="green")
    
    for table in schema.tables:
        relationships = [r for r in schema.relationships if r.source_table == table.name or r.target_table == table.name]
        table.add_row(
            table.name,
            str(len(table.columns)),
            str(len(relationships))
        )
    
    console.print(table)
    
    if Confirm.ask("🤔 Would you like to modify this schema?"):
        # Here you could implement schema modification logic
        console.print("[dim]Schema modification interface would be implemented here[/dim]")
    
    return schema

def _display_quality_report(report, output_format, verbose):
    """Display data quality report"""
    console.print(f"\n[bold blue]📊 Data Quality Report[/bold blue]")
    console.print(f"   Overall Score: [bold {'green' if report.overall_score >= 80 else 'yellow' if report.overall_score >= 60 else 'red'}]{report.overall_score:.1f}/100[/bold {'green' if report.overall_score >= 80 else 'yellow' if report.overall_score >= 60 else 'red'}]")
    
    # Issues summary
    if report.issues:
        console.print(f"\n[bold red]⚠️  Issues Found: {len(report.issues)}[/bold red]")
        
        issues_table = Table()
        issues_table.add_column("Issue", style="cyan")
        issues_table.add_column("Column", style="magenta")
        issues_table.add_column("Severity", style="red")
        issues_table.add_column("Affected Rows", style="yellow")
        
        for issue in report.issues[:10]:  # Show top 10 issues
            issues_table.add_row(
                issue.issue_type.value.replace('_', ' ').title(),
                issue.column,
                issue.severity.upper(),
                str(issue.affected_rows)
            )
        
        console.print(issues_table)
    
    # Recommendations summary
    if report.recommendations:
        console.print(f"\n[bold green]💡 Recommendations: {len(report.recommendations)}[/bold green]")
        
        rec_table = Table()
        rec_table.add_column("Action", style="cyan")
        rec_table.add_column("Column", style="magenta")
        rec_table.add_column("Confidence", style="green")
        
        for rec in report.recommendations[:5]:  # Show top 5 recommendations
            rec_table.add_row(
                rec.action.value.replace('_', ' ').title(),
                rec.column,
                f"{rec.confidence_score:.1%}"
            )
        
        console.print(rec_table)

async def _auto_apply_cleaning(cli_instance, file_content, file_type, report, original_path):
    """Automatically apply cleaning recommendations"""
    recommendations = [
        {
            "action": rec.action.value,
            "column": rec.column,
            "parameters": rec.parameters
        }
        for rec in report.recommendations[:5]  # Apply top 5 recommendations
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Applying cleaning recommendations...", total=None)
        
        try:
            result = await cli_instance.data_cleaner.apply_cleaning_recommendations(
                file_content, file_type, recommendations
            )
            
            progress.update(task, description="✅ Cleaning applied")
            
            # Save cleaned file
            cleaned_path = Path(original_path).with_suffix('.cleaned.csv')
            with open(cleaned_path, 'w') as f:
                f.write(result["cleaned_data"])
            
            console.print(f"\n[bold green]✨ Cleaned data saved to: {cleaned_path}[/bold green]")
            console.print(f"   📊 Quality improvement: {result['quality_improvement']['new_score']:.1f}/100")
            console.print(f"   🔧 Issues resolved: {result['quality_improvement']['issues_resolved']}")
            
        except Exception as e:
            progress.update(task, description=f"❌ Error: {str(e)}")
            console.print(f"[bold red]Error applying cleaning: {str(e)}[/bold red]")

async def _interactive_cleaning(cli_instance, file_content, file_type, report, original_path):
    """Interactive cleaning recommendation selection"""
    console.print("\n[bold yellow]🧹 Interactive Data Cleaning[/bold yellow]")
    
    selected_recommendations = []
    
    for i, rec in enumerate(report.recommendations, 1):
        console.print(f"\n[bold cyan]Recommendation {i}:[/bold cyan]")
        console.print(f"   Action: {rec.action.value.replace('_', ' ').title()}")
        console.print(f"   Column: {rec.column}")
        console.print(f"   Confidence: {rec.confidence_score:.1%}")
        console.print(f"   Reasoning: {rec.reasoning}")
        
        if Confirm.ask("   Apply this recommendation?"):
            selected_recommendations.append({
                "action": rec.action.value,
                "column": rec.column,
                "parameters": rec.parameters
            })
    
    if selected_recommendations:
        await _auto_apply_cleaning(cli_instance, file_content, file_type, 
                                 type('obj', (object,), {'recommendations': selected_recommendations})(), 
                                 original_path)

def _save_quality_report(report, output_path, output_format):
    """Save quality report to file"""
    output_path = Path(output_path)
    
    if output_format == 'json':
        # Convert report to JSON-serializable format
        report_dict = {
            "overall_score": report.overall_score,
            "metadata": report.metadata,
            "statistics": report.statistics,
            "issues": [
                {
                    "type": issue.issue_type.value,
                    "column": issue.column,
                    "severity": issue.severity,
                    "affected_rows": issue.affected_rows,
                    "description": issue.description
                }
                for issue in report.issues
            ],
            "recommendations": [
                {
                    "action": rec.action.value,
                    "column": rec.column,
                    "confidence": rec.confidence_score,
                    "reasoning": rec.reasoning
                }
                for rec in report.recommendations
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)

def _save_scaffold_files(scaffold_data, output_path, verbose):
    """Save API scaffold files to directory"""
    output_path.mkdir(parents=True, exist_ok=True)
    
    for component_type, components in scaffold_data['components'].items():
        if isinstance(components, list):
            for component in components:
                if 'filename' in component and 'content' in component:
                    file_path = output_path / component['filename']
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(file_path, 'w') as f:
                        f.write(component['content'])
                    
                    if verbose:
                        console.print(f"   📄 Created: {file_path}")

def _display_scaffold_preview(scaffold_data, verbose):
    """Display scaffold preview without saving"""
    console.print("\n[bold blue]🔍 API Scaffold Preview[/bold blue]")
    
    for component_type, components in scaffold_data['components'].items():
        if isinstance(components, list) and components:
            console.print(f"\n[bold cyan]{component_type.title()}:[/bold cyan]")
            
            for component in components[:2]:  # Show first 2 of each type
                if 'filename' in component:
                    console.print(f"   📄 {component['filename']}")
                    
                    if verbose and 'content' in component:
                        # Show first few lines of content
                        lines = component['content'].split('\n')[:10]
                        preview = '\n'.join(lines)
                        console.print(f"   [dim]{preview}...[/dim]")

def _get_syntax_lexer(format_name):
    """Get syntax highlighting lexer for format"""
    lexer_map = {
        'sqlalchemy': 'python',
        'sql': 'sql',
        'prisma': 'prisma',
        'typeorm': 'typescript',
        'django': 'python',
        'typescript': 'typescript',
        'json': 'json'
    }
    return lexer_map.get(format_name, 'text')

# ==================== NEW WEEK 7-8 CLI COMMANDS ====================

@cli.command()
@click.argument('schema_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for analysis report')
@click.option('--format', type=click.Choice(['json', 'yaml', 'table']), default='table', help='Output format')
@click.pass_context
def analyze(ctx, schema_file, output, format):
    """Analyze schema with AI critique system"""
    cli_instance = ctx.obj['cli']
    verbose = ctx.obj['verbose']
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Analyzing schema...", total=None)
        
        try:
            # Load schema
            schema_path = Path(schema_file)
            with open(schema_path) as f:
                if schema_path.suffix == '.json':
                    schema_data = json.load(f)
                elif schema_path.suffix in ['.yml', '.yaml']:
                    schema_data = yaml.safe_load(f)
                else:
                    console.print("[red]Error: Unsupported file format. Use JSON or YAML.[/red]")
                    return
            
            # Convert to SchemaResponse
            schema = SchemaResponse(**schema_data)
            
            # Run analysis
            async def run_analysis():
                return await cli_instance.ai_critic.analyze_schema(schema)
            
            analysis_report = asyncio.run(run_analysis())
            progress.update(task, description="Analysis complete!")
            
            if format == 'table':
                _display_analysis_table(analysis_report)
            else:
                report_data = _serialize_analysis_report(analysis_report)
                
                if output:
                    output_path = Path(output)
                    if format == 'json':
                        with open(output_path, 'w') as f:
                            json.dump(report_data, f, indent=2)
                    elif format == 'yaml':
                        with open(output_path, 'w') as f:
                            yaml.dump(report_data, f, default_flow_style=False)
                    console.print(f"[green]Analysis report saved to {output_path}[/green]")
                else:
                    if format == 'json':
                        console.print(json.dumps(report_data, indent=2))
                    elif format == 'yaml':
                        console.print(yaml.dump(report_data, default_flow_style=False))
                        
        except Exception as e:
            console.print(f"[red]Error analyzing schema: {e}[/red]")

@cli.command()
@click.argument('schema_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), help='Output file for merged schema')
@click.option('--strategy', type=click.Choice(['prefer_first', 'prefer_last', 'combine', 'auto_resolve']), 
              default='auto_resolve', help='Merge conflict resolution strategy')
@click.pass_context
def merge(ctx, schema_files, output, strategy):
    """Merge multiple schemas intelligently"""
    cli_instance = ctx.obj['cli']
    verbose = ctx.obj['verbose']
    
    if len(schema_files) < 2:
        console.print("[red]Error: At least 2 schema files required for merging[/red]")
        return
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Merging schemas...", total=len(schema_files))
        
        try:
            schemas = []
            
            # Load all schemas
            for schema_file in schema_files:
                schema_path = Path(schema_file)
                with open(schema_path) as f:
                    if schema_path.suffix == '.json':
                        schema_data = json.load(f)
                    elif schema_path.suffix in ['.yml', '.yaml']:
                        schema_data = yaml.safe_load(f)
                    else:
                        console.print(f"[yellow]Warning: Skipping unsupported file format: {schema_file}[/yellow]")
                        continue
                
                schemas.append(SchemaResponse(**schema_data))
                progress.update(task, advance=1)
            
            # Merge schemas
            async def run_merge():
                from core.schema_merger import MergeStrategy
                strategy_map = {
                    'prefer_first': MergeStrategy.PREFER_FIRST,
                    'prefer_last': MergeStrategy.PREFER_LAST,
                    'combine': MergeStrategy.COMBINE,
                    'auto_resolve': MergeStrategy.AUTO_RESOLVE
                }
                
                return await cli_instance.schema_merger.merge_schemas(
                    schemas,
                    strategy_overrides={},
                    merge_options={'default_strategy': strategy_map[strategy]}
                )
            
            merge_result = asyncio.run(run_merge())
            progress.update(task, description="Merge complete!")
            
            # Display results
            _display_merge_results(merge_result)
            
            # Save merged schema
            if output:
                output_path = Path(output)
                merged_data = _serialize_schema(merge_result.merged_schema)
                
                if output_path.suffix == '.json':
                    with open(output_path, 'w') as f:
                        json.dump(merged_data, f, indent=2)
                elif output_path.suffix in ['.yml', '.yaml']:
                    with open(output_path, 'w') as f:
                        yaml.dump(merged_data, f, default_flow_style=False)
                
                console.print(f"[green]Merged schema saved to {output_path}[/green]")
                
        except Exception as e:
            console.print(f"[red]Error merging schemas: {e}[/red]")

@cli.command()
@click.argument('project_dir', type=click.Path(), default='.')
@click.option('--author', prompt='Author name', help='Author name for version control')
@click.pass_context
def init_version_control(ctx, project_dir, author):
    """Initialize schema version control for a project"""
    cli_instance = ctx.obj['cli']
    
    project_path = Path(project_dir).resolve()
    version_control_path = project_path / '.schemasage' / 'versions'
    
    try:
        # Initialize version control
        version_control = SchemaVersionControl(str(version_control_path))
        
        # Look for existing schema file
        schema_file = None
        for pattern in ['schema.json', 'schema.yml', 'schema.yaml', 'database.json']:
            potential_file = project_path / pattern
            if potential_file.exists():
                schema_file = potential_file
                break
        
        if not schema_file:
            console.print("[yellow]No existing schema file found. Creating empty schema.[/yellow]")
            # Create minimal schema
            initial_schema = SchemaResponse(
                tables=[],
                relationships=[],
                schema_format="schemasage",
                metadata={"created_by": "cli", "version": "1.0.0"}
            )
        else:
            console.print(f"[blue]Found existing schema: {schema_file}[/blue]")
            with open(schema_file) as f:
                if schema_file.suffix == '.json':
                    schema_data = json.load(f)
                else:
                    schema_data = yaml.safe_load(f)
            initial_schema = SchemaResponse(**schema_data)
        
        # Initialize repository
        async def init_repo():
            return await version_control.initialize_repository(
                initial_schema, 
                author, 
                "Initial schema version"
            )
        
        version_id = asyncio.run(init_repo())
        
        console.print(f"[green]✅ Version control initialized![/green]")
        console.print(f"[blue]Initial version: {version_id}[/blue]")
        console.print(f"[blue]Repository: {version_control_path}[/blue]")
        
    except Exception as e:
        console.print(f"[red]Error initializing version control: {e}[/red]")

@cli.command()
@click.argument('schema_file', type=click.Path(exists=True))
@click.option('--message', '-m', prompt='Commit message', help='Commit message')
@click.option('--author', prompt='Author name', help='Author name')
@click.option('--tag', multiple=True, help='Tags for this version')
@click.option('--project-dir', type=click.Path(), default='.', help='Project directory')
@click.pass_context
def commit(ctx, schema_file, message, author, tag, project_dir):
    """Commit a new schema version"""
    cli_instance = ctx.obj['cli']
    
    project_path = Path(project_dir).resolve()
    version_control_path = project_path / '.schemasage' / 'versions'
    
    try:
        # Load schema
        with open(schema_file) as f:
            schema_path = Path(schema_file)
            if schema_path.suffix == '.json':
                schema_data = json.load(f)
            else:
                schema_data = yaml.safe_load(f)
        
        schema = SchemaResponse(**schema_data)
        
        # Initialize version control
        version_control = SchemaVersionControl(str(version_control_path))
        
        # Commit schema
        async def commit_schema():
            return await version_control.commit_schema(
                schema, author, message, list(tag)
            )
        
        version_id = asyncio.run(commit_schema())
        
        console.print(f"[green]✅ Schema committed![/green]")
        console.print(f"[blue]Version: {version_id}[/blue]")
        console.print(f"[blue]Message: {message}[/blue]")
        if tag:
            console.print(f"[blue]Tags: {', '.join(tag)}[/blue]")
            
    except Exception as e:
        console.print(f"[red]Error committing schema: {e}[/red]")

@cli.command()
@click.option('--project-dir', type=click.Path(), default='.', help='Project directory')
@click.option('--limit', type=int, help='Limit number of versions to show')
@click.option('--author', help='Filter by author')
@click.option('--tag', help='Filter by tag')
@click.pass_context
def versions(ctx, project_dir, limit, author, tag):
    """List schema versions"""
    project_path = Path(project_dir).resolve()
    version_control_path = project_path / '.schemasage' / 'versions'
    
    try:
        version_control = SchemaVersionControl(str(version_control_path))
        
        async def list_versions():
            return await version_control.list_versions(limit, author, tag)
        
        version_list = asyncio.run(list_versions())
        
        if not version_list:
            console.print("[yellow]No versions found[/yellow]")
            return
        
        # Display versions table
        table = Table(title="Schema Versions")
        table.add_column("Version ID", style="cyan")
        table.add_column("Author", style="green")
        table.add_column("Message", style="white")
        table.add_column("Timestamp", style="blue")
        table.add_column("Tags", style="yellow")
        table.add_column("Changes", style="magenta")
        
        for version in version_list:
            table.add_row(
                version.version_id[:12] + "...",
                version.author,
                version.message[:50] + ("..." if len(version.message) > 50 else ""),
                version.timestamp.strftime("%Y-%m-%d %H:%M"),
                ", ".join(version.tags) if version.tags else "-",
                str(len(version.changes))
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing versions: {e}[/red]")

@cli.command()
@click.argument('from_version')
@click.argument('to_version')
@click.option('--project-dir', type=click.Path(), default='.', help='Project directory')
@click.option('--sql', is_flag=True, help='Show SQL migration')
@click.pass_context
def diff(ctx, from_version, to_version, project_dir, sql):
    """Show differences between two schema versions"""
    project_path = Path(project_dir).resolve()
    version_control_path = project_path / '.schemasage' / 'versions'
    
    try:
        version_control = SchemaVersionControl(str(version_control_path))
        
        async def get_diff():
            return await version_control.get_version_diff(from_version, to_version)
        
        diff_result = asyncio.run(get_diff())
        
        # Display diff
        console.print(f"[bold blue]Differences: {from_version[:12]}...  →  {to_version[:12]}...[/bold blue]")
        
        if not diff_result.changes:
            console.print("[green]No changes found[/green]")
            return
        
        # Changes table
        table = Table(title="Schema Changes")
        table.add_column("Type", style="cyan")
        table.add_column("Impact", style="red")
        table.add_column("Item", style="white")
        table.add_column("Description", style="blue")
        
        for change in diff_result.changes:
            impact_style = {
                'breaking': 'red',
                'compatible': 'green',
                'minor': 'yellow',
                'cosmetic': 'blue'
            }.get(change.impact.value, 'white')
            
            table.add_row(
                change.change_type.value,
                f"[{impact_style}]{change.impact.value}[/{impact_style}]",
                change.affected_item,
                change.description
            )
        
        console.print(table)
        
        # Impact summary
        console.print(f"\n[bold]Impact Summary:[/bold]")
        for impact, count in diff_result.impact_summary.items():
            console.print(f"  {impact.value}: {count}")
        
        # SQL migration
        if sql and diff_result.migration_sql:
            console.print(f"\n[bold blue]Migration SQL:[/bold blue]")
            syntax = Syntax(diff_result.migration_sql, "sql", theme="monokai", line_numbers=True)
            console.print(syntax)
            
    except Exception as e:
        console.print(f"[red]Error getting diff: {e}[/red]")

@cli.command()
@click.option('--hours', type=int, default=1, help='Hours of performance data to show')
@click.pass_context
def performance(ctx, hours):
    """Show performance monitoring report"""
    try:
        from datetime import timedelta
        
        time_range = timedelta(hours=hours)
        report = performance_monitor.get_performance_report(time_range)
        health = performance_monitor.get_system_health()
        
        # System health
        console.print(f"[bold blue]System Health ({health['status'].upper()})[/bold blue]")
        
        if 'system' in health:
            sys_info = health['system']
            console.print(f"CPU: {sys_info['cpu_percent']:.1f}%")
            console.print(f"Memory: {sys_info['memory_percent']:.1f}% ({sys_info['memory_used_mb']:.1f} MB)")
            console.print(f"Active Operations: {health['active_operations']}")
            console.print(f"Recent Alerts: {health['alerts']}")
        
        # Performance metrics
        if report['metrics_summary']:
            console.print(f"\n[bold blue]Performance Metrics (Last {hours}h)[/bold blue]")
            
            metrics_table = Table()
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Count", style="white")
            metrics_table.add_column("Avg", style="green")
            metrics_table.add_column("Min", style="blue")
            metrics_table.add_column("Max", style="red")
            metrics_table.add_column("P95", style="yellow")
            
            for metric_type, stats in report['metrics_summary'].items():
                metrics_table.add_row(
                    metric_type,
                    str(stats['count']),
                    f"{stats['avg']:.3f}",
                    f"{stats['min']:.3f}",
                    f"{stats['max']:.3f}",
                    f"{stats['p95']:.3f}"
                )
            
            console.print(metrics_table)
        
        # Operation statistics
        if report['operation_statistics']:
            console.print(f"\n[bold blue]Operation Statistics[/bold blue]")
            
            ops_table = Table()
            ops_table.add_column("Operation", style="cyan")
            ops_table.add_column("Count", style="white")
            ops_table.add_column("Avg Time (s)", style="green")
            ops_table.add_column("Errors", style="red")
            
            for op_name, stats in report['operation_statistics'].items():
                error_rate = (stats['error_count'] / max(stats['count'], 1)) * 100
                ops_table.add_row(
                    op_name,
                    str(int(stats['count'])),
                    f"{stats['avg_time']:.3f}",
                    f"{int(stats['error_count'])} ({error_rate:.1f}%)"
                )
            
            console.print(ops_table)
        
        # Recommendations
        if report['recommendations']:
            console.print(f"\n[bold yellow]Recommendations[/bold yellow]")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                console.print(f"{i}. {rec}")
                
    except Exception as e:
        console.print(f"[red]Error getting performance report: {e}[/red]")

# Helper functions for new commands

def _display_analysis_table(analysis_report):
    """Display analysis report as a table"""
    console.print(f"[bold blue]Schema Analysis Report[/bold blue]")
    console.print(f"Overall Score: [bold green]{analysis_report.overall_score:.1f}/100[/bold green]")
    
    if analysis_report.critiques:
        table = Table(title="Schema Critiques")
        table.add_column("Category", style="cyan")
        table.add_column("Severity", style="red")
        table.add_column("Title", style="white")
        table.add_column("Priority", style="yellow")
        table.add_column("Confidence", style="green")
        
        for critique in analysis_report.critiques[:20]:  # Show top 20
            severity_style = {
                'critical': 'bright_red',
                'high': 'red',
                'medium': 'yellow',
                'low': 'blue',
                'info': 'green'
            }.get(critique.severity.value, 'white')
            
            table.add_row(
                critique.category.value,
                f"[{severity_style}]{critique.severity.value.upper()}[/{severity_style}]",
                critique.title,
                f"{critique.priority_score:.2f}",
                f"{critique.confidence_score:.2f}"
            )
        
        console.print(table)
    
    if analysis_report.strengths:
        console.print(f"\n[bold green]Strengths:[/bold green]")
        for strength in analysis_report.strengths:
            console.print(f"  ✅ {strength}")
    
    if analysis_report.recommendations:
        console.print(f"\n[bold yellow]Top Recommendations:[/bold yellow]")
        for i, rec in enumerate(analysis_report.recommendations[:5], 1):
            console.print(f"  {i}. {rec}")

def _display_merge_results(merge_result):
    """Display merge results"""
    console.print(f"[bold blue]Schema Merge Results[/bold blue]")
    console.print(f"Status: [bold {'green' if merge_result.success else 'red'}]{'SUCCESS' if merge_result.success else 'FAILED'}[/bold {'green' if merge_result.success else 'red'}]")
    console.print(f"Tables: {len(merge_result.merged_schema.tables)}")
    console.print(f"Relationships: {len(merge_result.merged_schema.relationships)}")
    console.print(f"Conflicts: {len(merge_result.conflicts)}")
    
    if merge_result.conflicts:
        table = Table(title="Merge Conflicts")
        table.add_column("Type", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Auto-Resolvable", style="green")
        
        for conflict in merge_result.conflicts:
            table.add_row(
                conflict.conflict_type.value,
                conflict.description,
                "✅" if conflict.auto_resolvable else "❌"
            )
        
        console.print(table)
    
    if merge_result.warnings:
        console.print(f"\n[bold yellow]Warnings:[/bold yellow]")
        for warning in merge_result.warnings:
            console.print(f"  ⚠️  {warning}")

def _serialize_analysis_report(analysis_report):
    """Serialize analysis report to dict"""
    return {
        "overall_score": analysis_report.overall_score,
        "critiques": [
            {
                "category": critique.category.value,
                "severity": critique.severity.value,
                "title": critique.title,
                "description": critique.description,
                "affected_tables": critique.affected_tables,
                "affected_columns": critique.affected_columns,
                "suggestion": critique.suggestion,
                "impact_assessment": critique.impact_assessment,
                "confidence_score": critique.confidence_score,
                "priority_score": critique.priority_score,
                "examples": critique.examples,
                "references": critique.references
            }
            for critique in analysis_report.critiques
        ],
        "strengths": analysis_report.strengths,
        "summary": analysis_report.summary,
        "recommendations": analysis_report.recommendations,
        "metadata": analysis_report.metadata
    }

def _serialize_schema(schema):
    """Serialize schema to dict"""
    return {
        "tables": [
            {
                "name": table.name,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.type,
                        "nullable": getattr(col, 'nullable', True),
                        "unique": getattr(col, 'unique', False),
                        "description": getattr(col, 'description', '')
                    }
                    for col in table.columns
                ],
                "description": table.description
            }
            for table in schema.tables
        ],
        "relationships": [
            {
                "source_table": rel.source_table,
                "source_column": rel.source_column,
                "target_table": rel.target_table,
                "target_column": rel.target_column,
                "type": rel.type
            }
            for rel in schema.relationships
        ],
        "schema_format": schema.schema_format,
        "metadata": schema.metadata
    }

if __name__ == '__main__':
    cli()
