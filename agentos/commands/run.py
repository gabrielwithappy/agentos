import typer
from rich.console import Console
from rich.prompt import Prompt

app = typer.Typer(help="Start the main agent session")
console = Console()

@app.callback(invoke_without_command=True)
def main():
    """Start the interactive agent chat session."""
    console.print("[bold blue]Starting AgentOS session... Type 'exit' or 'quit' to end.[/bold blue]")
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            if user_input.strip().lower() in ["exit", "quit"]:
                console.print("[bold yellow]Exiting AgentOS session...[/bold yellow]")
                break
                
            if not user_input.strip():
                continue
                
            console.print(f"[bold cyan]AgentOS:[/bold cyan] Received '{user_input}' (Mock response)")
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Exiting AgentOS session...[/bold yellow]")
            break
