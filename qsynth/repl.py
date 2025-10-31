"""REPL shell for interactive qsynth usage."""
import shlex
from pathlib import Path
from typing import Optional
import yaml

from qsynth import main as _main
from qsynth.models import Model


class QsynthRepl:
    """Interactive REPL shell for qsynth operations."""
    
    def __init__(self, yaml_file: str):
        """Initialize REPL with a YAML configuration file."""
        self.yaml_file = Path(yaml_file).absolute()
        if not self.yaml_file.exists():
            raise FileNotFoundError(f"YAML file not found: {self.yaml_file}")
        
        # Load models and experiments
        with open(self.yaml_file, 'r') as stream:
            self.config = yaml.safe_load(stream)
        
        self.models = [Model(**m) for m in self.config.get('models', [])]
        self.experiments = self.config.get('experiments', {})
        
        # REPL state
        self.last_result = None
        self.running = True
    
    def run(self):
        """Start the interactive REPL shell."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        
        console = Console()
        
        # Welcome banner
        console.print("\n")
        console.print(Panel(
            f"[bold cyan]Qsynth Interactive Shell[/bold cyan]\n"
            f"[dim]Loaded:[/dim] {self.yaml_file}\n"
            f"[dim]Models:[/dim] {len(self.models)}\n"
            f"[dim]Experiments:[/dim] {len(self.experiments)}",
            title="[green]Ready[/green]",
            border_style="green"
        ))
        console.print("\n[dim]Type 'help' for available commands or 'exit' to quit.[/dim]\n")
        
        # REPL loop
        while self.running:
            try:
                line = console.input("[bold green]qsynth>[/bold green] ").strip()
                if not line:
                    continue
                
                # Parse command
                parts = shlex.split(line)
                if not parts:
                    continue
                
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                # Execute command
                self._execute_command(console, command, args)
                
            except EOFError:
                # Ctrl+D
                console.print("\n[dim]Goodbye![/dim]\n")
                break
            except KeyboardInterrupt:
                # Ctrl+C
                console.print("\n[dim]Interrupted. Type 'exit' to quit.[/dim]\n")
                continue
            except Exception as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}\n")
    
    def _execute_command(self, console, command: str, args: list):
        """Execute a REPL command."""
        cmd_lower = command.lower()
        
        if cmd_lower == 'exit' or cmd_lower == 'quit':
            self.running = False
            console.print("[dim]Goodbye![/dim]\n")
        
        elif cmd_lower == 'help':
            self._cmd_help(console)
        
        elif cmd_lower == 'list' or cmd_lower == 'ls':
            self._cmd_list(console)
        
        elif cmd_lower == 'models':
            self._cmd_models(console, args)
        
        elif cmd_lower == 'schemas':
            self._cmd_schemas(console, args)
        
        elif cmd_lower == 'experiments' or cmd_lower == 'exps':
            self._cmd_experiments(console)
        
        elif cmd_lower == 'describe':
            self._cmd_describe(console, args)
        
        elif cmd_lower == 'run':
            self._cmd_run(console, args)
        
        elif cmd_lower == 'types':
            self._cmd_types(console, args)
        
        elif cmd_lower == 'info':
            self._cmd_info(console, args)
        
        elif cmd_lower == 'preview':
            self._cmd_preview(console, args)
        
        elif cmd_lower == 'clear':
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
        
        else:
            console.print(f"[bold yellow]Unknown command:[/bold yellow] {command}")
            console.print("[dim]Type 'help' for available commands.[/dim]\n")
    
    def _cmd_help(self, console):
        """Show help message."""
        from rich.panel import Panel
        from rich.table import Table
        
        help_text = """
[cyan]Available Commands:[/cyan]

[bold]Information:[/bold]
  help              - Show this help message
  list/ls           - List models, schemas, and experiments
  models            - Show all models
  schemas           - Show schemas (optionally filtered by model)
  experiments/exps  - Show all experiments
  describe          - Describe a specific model, schema, or experiment
  
[bold]Operations:[/bold]
  run               - Run experiments (all or specific)
  preview           - Preview generated data in a table
  types             - List or search for Faker provider types
  info <type>       - Show detailed information about a Faker type
  
[bold]Utilities:[/bold]
  clear             - Clear the screen
  exit/quit         - Exit the REPL shell

[dim]Examples:[/dim]
  list                        - List everything
  models                      - Show all models
  schemas moneta              - Show schemas in 'moneta' model
  describe model moneta       - Describe the 'moneta' model
  describe schema clients     - Describe the 'clients' schema
  preview                     - Preview all generated data
  preview moneta              - Preview data from 'moneta' model
  preview moneta clients      - Preview 'clients' schema from 'moneta' model
  preview --rows 20           - Preview with 20 rows per table
  run                         - Run all experiments
  run write_csv               - Run specific experiment
  types --all                 - List all Faker types
  types --find random         - Search for random types
  info random_int             - Info about random_int type
"""
        console.print(Panel(help_text.strip(), title="[bold]Qsynth REPL Commands[/bold]", border_style="cyan"))
        console.print()
    
    def _cmd_list(self, console):
        """List all models, schemas, and experiments."""
        _main.list_schema_content(self.yaml_file, self.config)
    
    def _cmd_models(self, console, args):
        """List all models."""
        console.print(f"\n[bold cyan]Models ({len(self.models)}):[/bold cyan]\n")
        for model in self.models:
            locales_str = model.locales if isinstance(model.locales, str) else ', '.join(model.locales)
            console.print(f"  [green]{model.name}[/green] - {len(model.schemas)} schema(s), locale(s): {locales_str}")
        console.print()
    
    def _cmd_schemas(self, console, args):
        """List schemas, optionally filtered by model."""
        if args:
            model_name = args[0]
            filtered_models = [m for m in self.models if m.name == model_name]
            if filtered_models:
                models_to_show = filtered_models
            else:
                console.print(f"[bold red]Model '{model_name}' not found.[/bold red]\n")
                return
        else:
            models_to_show = self.models
        
        for model in models_to_show:
            console.print(f"\n[bold cyan]Schemas in '{model.name}' ({len(model.schemas)}):[/bold cyan]\n")
            for schema in model.schemas:
                rows_str = str(schema.rows) if isinstance(schema.rows, int) else f"{schema.rows.min}-{schema.rows.max} (random)"
                desc = f" - {schema.description}" if schema.description else ""
                console.print(f"  [green]{schema.name}[/green]: {rows_str} rows{desc}")
        console.print()
    
    def _cmd_experiments(self, console):
        """List all experiments."""
        console.print(f"\n[bold cyan]Experiments ({len(self.experiments)}):[/bold cyan]\n")
        for exp_name, exp_config in sorted(self.experiments.items()):
            exp_type = exp_config.get('type', 'unknown')
            console.print(f"  [cyan]{exp_name}[/cyan] - type: [yellow]{exp_type}[/yellow]")
        console.print()
    
    def _cmd_describe(self, console, args):
        """Describe a model, schema, or all experiments."""
        if not args:
            console.print("[bold yellow]Usage:[/bold yellow] describe <model|schema|experiments> [name]\n")
            return
        
        target = args[0].lower()
        
        if target == 'experiments' or target == 'experiment':
            _main.describe_experiments(self.yaml_file)
        
        elif target == 'model' and len(args) > 1:
            model_name = args[1]
            _main.show_schema_info(self.yaml_file, model_name=model_name)
        
        elif target == 'schema' and len(args) > 1:
            schema_name = args[1]
            # Try to find the schema across all models
            found = False
            for model in self.models:
                if any(s.name == schema_name for s in model.schemas):
                    _main.show_schema_info(self.yaml_file, model_name=model.name, schema_name=schema_name)
                    found = True
                    break
            
            if not found:
                console.print(f"[bold red]Schema '{schema_name}' not found in any model.[/bold red]\n")
        
        else:
            console.print("[bold yellow]Usage:[/bold yellow] describe <model|schema|experiments> [name]\n")
    
    def _cmd_run(self, console, args):
        """Run experiments."""
        if not args:
            # Run all experiments
            console.print("[bold cyan]Running all experiments...[/bold cyan]\n")
            _main.run_all_experiments(self.yaml_file)
        else:
            # Run specific experiments
            console.print(f"[bold cyan]Running experiments: {', '.join(args)}[/bold cyan]\n")
            _main.run_experiments(self.yaml_file, *args)
    
    def _cmd_types(self, console, args):
        """List or search for Faker provider types."""
        # Parse args
        find_arg = None
        all_arg = False
        
        i = 0
        while i < len(args):
            if args[i] == '--find' and i + 1 < len(args):
                find_arg = args[i + 1]
                i += 2
            elif args[i] == '--all':
                all_arg = True
                i += 1
            else:
                i += 1
        
        if find_arg:
            _main.list_providers(find_arg)
        elif all_arg:
            _main.list_providers()
        else:
            console.print("[bold yellow]Usage:[/bold yellow] types [--all | --find <pattern>]\n")
    
    def _cmd_info(self, console, args):
        """Show detailed info about a Faker type."""
        if not args:
            console.print("[bold yellow]Usage:[/bold yellow] info <type_name>\n")
            return
        
        type_name = args[0]
        _main.show_type_info(type_name)
    
    def _cmd_preview(self, console, args):
        """Preview generated data."""
        # Parse args for model, schema, and rows
        model_name = None
        schema_name = None
        rows = 10
        
        i = 0
        while i < len(args):
            if args[i] == '--rows' and i + 1 < len(args):
                try:
                    rows = int(args[i + 1])
                    i += 2
                except ValueError:
                    console.print("[bold red]Error:[/bold red] --rows must be an integer\n")
                    return
            elif args[i] == '-r' and i + 1 < len(args):
                try:
                    rows = int(args[i + 1])
                    i += 2
                except ValueError:
                    console.print("[bold red]Error:[/bold red] -r must be an integer\n")
                    return
            elif not model_name:
                model_name = args[i]
                i += 1
            elif not schema_name:
                schema_name = args[i]
                i += 1
            else:
                i += 1
        
        _main.preview_data(str(self.yaml_file), model_name=model_name, schema_name=schema_name, rows=rows)

