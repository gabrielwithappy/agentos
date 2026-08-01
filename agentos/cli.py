import sys

import typer
from rich.console import Console

try:
    from agentos.observability.setup import setup_observability
    setup_observability()
except ImportError:
    pass

from agentos.commands import setup, run, harness, doctor, skill, agent, llm, session, hook, project, dashboard, knowledge
from agentos.terminal.paths import read_preferred_provider
from agentos.terminal.tui import run_tui

app = typer.Typer(
    help="AgentOS CLI - Manage and run your AI agents",
    invoke_without_command=True,
    no_args_is_help=False,
    add_completion=False,
)

console = Console()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Print version and exit."),
    provider: str | None = typer.Option(None, "--provider", help="Interactive provider."),
    yolo: bool = typer.Option(False, "--yolo", help="Skip write/edit/bash approval prompts (use with care)."),
):
    if version:
        console.print("AgentOS CLI version 0.1.0")
        raise typer.Exit(0)
    if ctx.invoked_subcommand is not None:
        return
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        typer.echo(
            'Interactive mode requires a TTY. Next: agentos run --once "<prompt>".',
            err=True,
        )
        raise typer.Exit(2)
    selected_provider = provider or read_preferred_provider() or "mock"
    raise typer.Exit(run_tui(provider=selected_provider, yolo=yolo))


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
app.add_typer(agent.app, name="agent", help="Manage agents")
app.add_typer(llm.app, name="llm", help="Inspect LLM provider status")
app.add_typer(session.app, name="session", help="Manage sessions")
app.add_typer(hook.app, name="hook", help="Manage hooks")
app.add_typer(project.app, name="project", help="Reflect global AgentOS resources into a project")
app.add_typer(dashboard.app, name="dashboard", help="Sync exec-plan documents to an external dashboard")
app.add_typer(knowledge.app, name="knowledge", help="Store, publish, search, and cite project knowledge")

@app.command()
def version():
    """Print the version of AgentOS CLI."""
    console.print("[bold green]AgentOS CLI version 0.1.0[/bold green]")

if __name__ == "__main__":
    app()
