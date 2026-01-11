"""
Generate BMR Recovery Incident Dataset
Creates complete synthetic data for the BMR recovery scenario
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path to import generators
sys.path.append(str(Path(__file__).parent))

from generators.incidents import IncidentGenerator, IncidentScenario

console = Console()


def main():
    """Generate BMR recovery incident dataset"""
    
    console.print("\n[bold cyan]WardenXT - BMR Recovery Incident Generator[/bold cyan]\n")
    
    # Load BMR scenario
    scenario_path = Path(__file__).parent / "scenarios" / "bmr_recovery.yaml"
    
    if not scenario_path.exists():
        console.print(f"[red]✗ Scenario file not found: {scenario_path}[/red]")
        return False
    
    console.print(f"[green]✓ Loading scenario:[/green] {scenario_path.name}")
    
    try:
        scenario = IncidentScenario.from_yaml(scenario_path)
        console.print(f"[cyan]  Incident ID:[/cyan] {scenario.incident_id}")
        console.print(f"[cyan]  Title:[/cyan] {scenario.title}")
        console.print(f"[cyan]  Severity:[/cyan] {scenario.severity}")
        console.print(f"[cyan]  Duration:[/cyan] {scenario.duration_minutes} minutes")
        console.print(f"[cyan]  Services:[/cyan] {', '.join(scenario.services_affected)}")
    except Exception as e:
        console.print(f"[red]✗ Failed to load scenario: {e}[/red]")
        return False
    
    # Generate incident data
    console.print("\n[bold]Generating incident dataset...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Generating logs and metrics...", total=None)
        
        try:
            generator = IncidentGenerator(scenario)
            dataset = generator.generate()
            
            progress.update(task, description="✓ Generation complete!")
            
        except Exception as e:
            console.print(f"\n[red]✗ Generation failed: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
            return False
    
    # Display statistics
    console.print("\n[bold green]Dataset Statistics:[/bold green]")
    console.print(f"  • Log entries: {len(dataset.logs)}")
    console.print(f"  • Metric points: {len(dataset.metrics)}")
    console.print(f"  • Timeline events: {len(dataset.timeline)}")
    
    # Calculate data size
    import json
    logs_size = sum(len(log.to_json()) for log in dataset.logs)
    metrics_size = sum(len(metric.to_json()) for metric in dataset.metrics)
    total_size_mb = (logs_size + metrics_size) / (1024 * 1024)
    
    console.print(f"  • Total data size: {total_size_mb:.2f} MB")
    
    # Save dataset
    output_dir = Path(__file__).parent / "output"
    console.print(f"\n[bold]Saving to:[/bold] {output_dir}")
    
    try:
        dataset.save_to_directory(output_dir)
        console.print("\n[bold green]✓ BMR Recovery incident dataset generated successfully![/bold green]")
        
        # Show file locations
        incident_dir = output_dir / scenario.incident_id
        console.print(f"\n[cyan]Generated files:[/cyan]")
        console.print(f"  📄 {incident_dir / 'logs.jsonl'}")
        console.print(f"  📊 {incident_dir / 'metrics.jsonl'}")
        console.print(f"  ⏱️  {incident_dir / 'timeline.json'}")
        console.print(f"  📋 {incident_dir / 'summary.json'}")
        
    except Exception as e:
        console.print(f"\n[red]✗ Failed to save dataset: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    console.print()  # Empty line
    sys.exit(0 if success else 1)