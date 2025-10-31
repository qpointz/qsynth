"""REPL shell for interactive qsynth usage."""
import shlex
from pathlib import Path
from typing import Optional, List
import yaml
import inspect

from qsynth import main as _main
from qsynth.models import Model


class QsynthCompleter:
    """Auto-completion completer for qsynth REPL commands."""
    
    def __init__(self, repl_instance):
        """Initialize completer with reference to REPL instance."""
        self.repl = repl_instance
        self._faker_types = None  # Cache for faker types
    
    async def get_completions_async(self, document, complete_event):
        """Async version of get_completions."""
        # Delegate to sync version - prompt_toolkit will handle the async wrapping
        for completion in self.get_completions(document, complete_event):
            yield completion
    
    def _get_faker_types(self) -> List[str]:
        """Get list of all available Faker provider types."""
        if self._faker_types is None:
            faker = _main.create_faker()
            providers = []
            for attr in dir(faker):
                if attr.startswith('_'):
                    continue
                try:
                    # Safely check if attribute is callable
                    obj = getattr(faker, attr, None)
                    if obj is not None and callable(obj):
                        providers.append(attr)
                except (TypeError, AttributeError):
                    # Skip attributes that raise errors when accessed
                    continue
            self._faker_types = sorted(providers)
        return self._faker_types
    
    def _get_commands(self) -> List[str]:
        """Get list of all available commands."""
        return [
            'help', 'list', 'ls', 'models', 'schemas', 'experiments', 'exps',
            'describe', 'run', 'preview', 'types', 'info', 'test', 'clear', 'exit', 'quit'
        ]
    
    def _get_model_names(self) -> List[str]:
        """Get list of all model names."""
        return [model.name for model in self.repl.models]
    
    def _get_schema_names(self, model_name: Optional[str] = None) -> List[str]:
        """Get list of schema names, optionally filtered by model."""
        schemas = []
        for model in self.repl.models:
            if model_name is None or model.name == model_name:
                schemas.extend([schema.name for schema in model.schemas])
        return sorted(set(schemas))
    
    def _get_experiment_names(self) -> List[str]:
        """Get list of all experiment names."""
        return sorted(self.repl.experiments.keys())
    
    def _matches_filter(self, candidate: str, filter_text: str) -> bool:
        """Check if candidate matches filter text (case-insensitive, supports partial match)."""
        if not filter_text:
            return True
        candidate_lower = candidate.lower()
        filter_lower = filter_text.lower()
        # Support both prefix matching (preferred) and substring matching
        return candidate_lower.startswith(filter_lower) or filter_lower in candidate_lower
    
    def _get_completion_priority(self, candidate: str, filter_text: str) -> int:
        """Return priority for completion (lower = higher priority)."""
        if not filter_text:
            return 1
        candidate_lower = candidate.lower()
        filter_lower = filter_text.lower()
        if candidate_lower.startswith(filter_lower):
            return 0  # Prefix match has highest priority
        elif filter_lower in candidate_lower:
            return 1  # Substring match has lower priority
        return 2
    
    def get_completions(self, document, complete_event):
        """Get completions for the current input with incremental search support."""
        from prompt_toolkit.completion import Completion
        
        text = document.text_before_cursor
        words = []
        
        # Try to parse words, handling quoted strings
        try:
            words = shlex.split(text) if text.strip() else []
        except ValueError:
            # If parsing fails (unclosed quote), return empty
            return
        
        # If we're in the middle of a quoted string, don't complete
        if text.count('"') % 2 == 1 or text.count("'") % 2 == 1:
            return
        
        # First word - command completion
        if len(words) == 0 or (len(words) == 1 and not text.endswith(' ')):
            word_before_cursor = document.get_word_before_cursor(WORD=True)
            if not word_before_cursor:
                word_before_cursor = ""
            commands = self._get_commands()
            # Sort by priority (prefix matches first, then substring matches)
            matching_commands = [
                (cmd, self._get_completion_priority(cmd, word_before_cursor))
                for cmd in commands
                if self._matches_filter(cmd, word_before_cursor)
            ]
            matching_commands.sort(key=lambda x: x[1])  # Sort by priority
            for cmd, _ in matching_commands:
                yield Completion(cmd, start_position=-len(word_before_cursor))
            return
        
        command = words[0].lower()
        current_word = document.get_word_before_cursor(WORD=True)
        if not current_word:
            current_word = ""
        
        # Check if we're at a new argument position
        is_new_arg = text.endswith(' ') or len(words) > 1
        
        # Command-specific completions
        if command == 'schemas':
            # schemas [model_name]
            if len(words) == 2 or (len(words) == 1 and is_new_arg):
                for model in self._get_model_names():
                    if self._matches_filter(model, current_word):
                        yield Completion(model, start_position=-len(current_word))
        
        elif command == 'describe':
            # describe [model|schema|experiments] [name]
            if len(words) == 1 or (len(words) == 2 and not is_new_arg):
                # Complete: model, schema, experiments
                options = ['model', 'schema', 'experiments']
                for opt in options:
                    if self._matches_filter(opt, current_word):
                        yield Completion(opt, start_position=-len(current_word))
            
            elif len(words) == 2 and words[1].lower() == 'model':
                # describe model [model_name]
                if is_new_arg or len(words) == 3:
                    for model in self._get_model_names():
                        if self._matches_filter(model, current_word):
                            yield Completion(model, start_position=-len(current_word))
            
            elif len(words) == 2 and words[1].lower() == 'schema':
                # describe schema [schema_name]
                if is_new_arg or len(words) == 3:
                    for schema in self._get_schema_names():
                        if self._matches_filter(schema, current_word):
                            yield Completion(schema, start_position=-len(current_word))
        
        elif command == 'run':
            # run [experiment1] [experiment2] ...
            if len(words) >= 1:
                experiments = self._get_experiment_names()
                # Sort by priority (prefix matches first)
                matching_exps = [
                    (exp, self._get_completion_priority(exp, current_word))
                    for exp in experiments
                    if self._matches_filter(exp, current_word)
                ]
                matching_exps.sort(key=lambda x: x[1])
                for exp, _ in matching_exps:
                    yield Completion(exp, start_position=-len(current_word))
        
        elif command == 'preview':
            # preview [model] [schema] or preview --rows [number]
            i = 1
            model_found = False
            schema_found = False
            in_rows_flag = False
            
            # Parse arguments to understand context
            while i < len(words):
                if words[i] in ['--rows', '-r']:
                    in_rows_flag = True
                    break
                elif not model_found and words[i] not in ['--rows', '-r']:
                    model_found = True
                    i += 1
                elif model_found and not schema_found:
                    schema_found = True
                    break
                else:
                    i += 1
            
            if not model_found and not in_rows_flag:
                # Complete model names or flags
                flags = ['--rows', '-r']
                for flag in flags:
                    if self._matches_filter(flag, current_word):
                        yield Completion(flag, start_position=-len(current_word))
                
                for model in self._get_model_names():
                    if self._matches_filter(model, current_word):
                        yield Completion(model, start_position=-len(current_word))
            
            elif model_found and not schema_found and not in_rows_flag:
                # Complete schema names for the model
                model_name = words[1] if len(words) > 1 else None
                for schema in self._get_schema_names(model_name):
                    if self._matches_filter(schema, current_word):
                        yield Completion(schema, start_position=-len(current_word))
        
        elif command == 'types':
            # types [--all | --find <pattern>]
            if len(words) == 1 or (len(words) == 2 and not is_new_arg):
                flags = ['--all', '--find']
                for flag in flags:
                    if self._matches_filter(flag, current_word):
                        yield Completion(flag, start_position=-len(current_word))
            
            elif len(words) >= 2 and words[1] == '--find':
                # Complete faker types after --find (support incremental search)
                if len(words) == 2 or (len(words) == 3 and not is_new_arg):
                    # Allow pattern matching on faker types
                    faker_types = self._get_faker_types()
                    matching_types = [
                        (ftype, self._get_completion_priority(ftype, current_word))
                        for ftype in faker_types
                        if self._matches_filter(ftype, current_word)
                    ]
                    matching_types.sort(key=lambda x: x[1])
                    for ftype, _ in matching_types:
                        yield Completion(ftype, start_position=-len(current_word))
        
        elif command == 'info':
            # info <type_name>
            if len(words) == 1 or (len(words) == 2 and not is_new_arg):
                faker_types = self._get_faker_types()
                # Sort by priority (prefix matches first) - important for large lists
                matching_types = [
                    (ftype, self._get_completion_priority(ftype, current_word))
                    for ftype in faker_types
                    if self._matches_filter(ftype, current_word)
                ]
                matching_types.sort(key=lambda x: x[1])
                for ftype, _ in matching_types:
                    yield Completion(ftype, start_position=-len(current_word))
        
        elif command == 'test':
            # test <type_name>
            if len(words) == 1 or (len(words) == 2 and not is_new_arg):
                faker_types = self._get_faker_types()
                # Sort by priority (prefix matches first) - important for large lists
                matching_types = [
                    (ftype, self._get_completion_priority(ftype, current_word))
                    for ftype in faker_types
                    if self._matches_filter(ftype, current_word)
                ]
                matching_types.sort(key=lambda x: x[1])
                for ftype, _ in matching_types:
                    yield Completion(ftype, start_position=-len(current_word))
        
        elif command == 'models':
            # No arguments
            pass
        
        elif command in ['experiments', 'exps', 'list', 'ls', 'help', 'clear', 'exit', 'quit']:
            # No arguments
            pass


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
        
        # Initialize completer
        self.completer = QsynthCompleter(self)
    
    def run(self):
        """Start the interactive REPL shell."""
        from rich.console import Console
        from rich.panel import Panel
        from prompt_toolkit import PromptSession
        from prompt_toolkit.styles import Style
        
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
        console.print("\n[dim]Type 'help' for available commands or 'exit' to quit.[/dim]")
        console.print("[dim]Auto-completion with incremental search enabled - suggestions appear as you type.[/dim]\n")
        
        # Configure prompt session with completer and incremental search
        from prompt_toolkit.history import InMemoryHistory
        from prompt_toolkit.key_binding import KeyBindings
        
        # Create key bindings for better navigation
        kb = KeyBindings()
        
        # Configure prompt session with completer
        session = PromptSession(
            completer=self.completer,
            complete_while_typing=True,  # Show suggestions as you type
            complete_in_thread=True,  # Run completion in separate thread for better performance
            enable_open_in_editor=True,  # Allow opening in editor
            history=InMemoryHistory(),
            key_bindings=kb,
        )
        
        # REPL loop
        while self.running:
            try:
                # Get input with auto-completion
                line = session.prompt("qsynth> ", style=Style.from_dict({
                    'prompt': 'ansigreen bold',
                })).strip()
                
                if not line:
                    continue
                
                # Parse command
                parts = shlex.split(line)
                if not parts:
                    continue
                
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                # Execute command
                self._execute_command(console, command, args, session)
                
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
    
    def _execute_command(self, console, command: str, args: list, session=None):
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
        
        elif cmd_lower == 'test':
            self._cmd_test(console, args, session)
        
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
  test <type>       - Test a Faker type by generating 10 sample values with custom parameters
  
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
    
    def _cmd_test(self, console, args, session):
        """Test a Faker type by generating sample values with custom parameters."""
        from rich.table import Table
        
        if not args:
            console.print("[bold yellow]Usage:[/bold yellow] test <type_name>\n")
            console.print("[dim]Example: test random_int[/dim]\n")
            return
        
        type_name = args[0]
        faker = _main.create_faker()
        
        # Check if type exists
        if not hasattr(faker, type_name):
            console.print(f"[bold red]Error:[/bold red] Type '[yellow]{type_name}[/yellow]' not found.\n")
            console.print("[dim]Use 'info <type_name>' to see available types.[/dim]\n")
            return
        
        # Get the method
        try:
            method = getattr(faker, type_name)
            if not callable(method):
                console.print(f"[bold red]Error:[/bold red] '[yellow]{type_name}[/yellow]' is not a callable method.\n")
                return
            
            # Get signature
            sig = inspect.signature(method)
            params = sig.parameters
            
            # Collect parameters
            kwargs = {}
            required_params = []
            optional_params = []
            
            for param_name, param in params.items():
                if param_name == 'self':
                    continue
                if param.default == inspect.Parameter.empty:
                    required_params.append((param_name, param))
                else:
                    optional_params.append((param_name, param, param.default))
            
            # Show parameter info
            console.print(f"\n[bold cyan]Testing type:[/bold cyan] [yellow]{type_name}[/yellow]\n")
            
            if required_params or optional_params:
                console.print("[bold]Parameters:[/bold]\n")
                
                # Prompt for required parameters
                for param_name, param in required_params:
                    param_type = "-"
                    if param.annotation != inspect.Parameter.empty:
                        param_type = param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)
                    
                    console.print(f"[cyan]{param_name}[/cyan] ({param_type}) [bold red]*required*[/bold red]")
                    
                    while True:
                        try:
                            value_str = session.prompt(f"  Enter {param_name}: ").strip()
                            
                            if not value_str:
                                console.print(f"[yellow]  Parameter {param_name} is required. Please enter a value.[/yellow]")
                                continue
                            
                            # Try to convert to appropriate type
                            value = self._parse_parameter_value(value_str, param.annotation)
                            kwargs[param_name] = value
                            break
                        except (ValueError, TypeError) as e:
                            console.print(f"[red]  Invalid value: {e}. Please try again.[/red]")
                        except (EOFError, KeyboardInterrupt):
                            console.print("\n[dim]Test cancelled.[/dim]\n")
                            return
                
                # Prompt for optional parameters
                for param_name, param, default_value in optional_params:
                    param_type = "-"
                    if param.annotation != inspect.Parameter.empty:
                        param_type = param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)
                    
                    default_str = str(default_value)
                    console.print(f"[cyan]{param_name}[/cyan] ({param_type}) [dim]default: {default_str}[/dim]")
                    
                    try:
                        value_str = session.prompt(f"  Enter {param_name} (default: {default_str}, press Enter to use default): ").strip()
                        
                        if value_str:
                            # Try to convert to appropriate type
                            try:
                                value = self._parse_parameter_value(value_str, param.annotation)
                                kwargs[param_name] = value
                            except (ValueError, TypeError):
                                # If conversion fails, use default
                                kwargs[param_name] = default_value
                                console.print(f"[dim]  Using default value: {default_str}[/dim]")
                        else:
                            kwargs[param_name] = default_value
                    except (EOFError, KeyboardInterrupt):
                        console.print("\n[dim]Test cancelled.[/dim]\n")
                        return
            else:
                console.print("[dim]No parameters required.[/dim]\n")
            
            # Generate 10 values
            console.print(f"\n[bold green]Generating 10 sample values...[/bold green]\n")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Value", style="green", overflow="fold")
            
            for i in range(1, 11):
                try:
                    value = method(**kwargs)
                    value_str = str(value)
                    # Truncate very long values
                    if len(value_str) > 80:
                        value_str = value_str[:77] + "..."
                    table.add_row(str(i), value_str)
                except Exception as e:
                    table.add_row(str(i), f"[red]Error: {e}[/red]")
            
            console.print(table)
            console.print()
            
            # Output YAML configuration snippet
            console.print("[bold cyan]YAML Configuration:[/bold cyan]\n")
            console.print("[dim]# Copy-paste this into your YAML file[/dim]")
            console.print("[dim]# Replace 'attribute_name' with your desired attribute name[/dim]\n")
            
            # Build YAML structure
            yaml_lines = ["- name: attribute_name"]
            yaml_lines.append(f"  type: {type_name}")
            
            if kwargs:
                yaml_lines.append("  params:")
                for param_name, param_value in sorted(kwargs.items()):
                    yaml_value = self._format_yaml_value(param_value)
                    yaml_lines.append(f"    {param_name}: {yaml_value}")
            
            yaml_text = "\n".join(yaml_lines)
            
            # Display with syntax highlighting
            from rich.syntax import Syntax
            console.print(Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False))
            console.print()
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}\n")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]\n")
    
    def _format_yaml_value(self, value: any) -> str:
        """Format a Python value for YAML output."""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, str):
            # Quote strings that might need quoting
            if any(c in value for c in [' ', ':', '#', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
                return f'"{value}"'
            return value
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            items = [self._format_yaml_value(item) for item in value]
            return f"[{', '.join(items)}]"
        elif value is None:
            return "null"
        else:
            return str(value)
    
    def _parse_parameter_value(self, value_str: str, annotation) -> any:
        """Parse a string value to the appropriate type based on annotation."""
        if not annotation or annotation == inspect.Parameter.empty:
            # Try to infer type from value
            try:
                # Try int
                if '.' not in value_str:
                    return int(value_str)
                # Try float
                return float(value_str)
            except ValueError:
                # Return as string
                return value_str
        
        # Convert based on annotation
        annotation_str = str(annotation)
        
        if 'int' in annotation_str or annotation == int:
            return int(value_str)
        elif 'float' in annotation_str or 'double' in annotation_str or annotation == float:
            return float(value_str)
        elif 'bool' in annotation_str or annotation == bool:
            return value_str.lower() in ('true', '1', 'yes', 'on')
        elif 'str' in annotation_str or annotation == str:
            return value_str
        else:
            # Try common conversions
            try:
                if '.' not in value_str:
                    return int(value_str)
                return float(value_str)
            except ValueError:
                return value_str

