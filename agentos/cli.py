import typer
from rich.console import Console

from agentos.commands import setup, run, harness, doctor, skill

app = typer.Typer(
    help="AgentOS CLI - Manage and run your AI agents",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()

# Add subcommands as commands if they are single actions
app.command(name="setup", help="Initialize AgentOS environment")(setup.main)
app.command(name="run", help="Start the main agent session")(run.main)
app.command(
    name="harness", 
    help="Run the core harness loop",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)(harness.main)
app.command(name="doctor", help="Check system dependencies and state")(doctor.main)

# Add subcommands that have their own subcommands as Typer groups
app.add_typer(skill.app, name="skill", help="Manage agent skills")

@app.command()
def version():
    """Print the version of AgentOS CLI."""
    console.print("[bold green]AgentOS CLI version 0.1.0[/bold green]")

if __name__ == "__main__":
    app()
