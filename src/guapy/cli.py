"""CLI entry point for guapy server using Typer and Rich."""

import logging

import typer
from rich import print as rich_print
from rich.console import Console

from .config import get_config
from .models import ClientOptions, CryptConfig, GuacdOptions
from .server import create_server

app = typer.Typer(help="Guapy: Python Guacamole WebSocket server CLI")
console = Console()


@app.command()
def run(
    host: str = typer.Option(None, help="Host to bind the server (overrides config)"),
    port: int = typer.Option(None, help="Port to bind the server (overrides config)"),
    guacd_host: str = typer.Option(None, help="guacd host (overrides config)"),
    guacd_port: int = typer.Option(None, help="guacd port (overrides config)"),
    secret_key: str = typer.Option(
        None, help="Secret key for authentication (overrides config)"
    ),
    max_connections: int = typer.Option(
        None, help="Maximum concurrent connections (overrides config)"
    ),
    crypt_cypher: str = typer.Option(
        "AES-256-CBC", help="Encryption cypher for tokens (overrides config)"
    ),
    inactivity_time: int = typer.Option(
        10000, help="Max inactivity time in ms (overrides config)"
    ),
    config_file: str = typer.Option(
        None, help="Path to config file (default: config.json)"
    ),
    log_level: str = typer.Option(
        "debug", help="Log level (debug, info, warning, error, critical)"
    ),
) -> None:
    """Run the Guapy server."""
    try:
        config_kwargs = {
            "host": host,
            "port": port,
            "guacd_host": guacd_host,
            "guacd_port": guacd_port,
            "secret_key": secret_key,
            "max_connections": max_connections,
        }
        config_kwargs = {k: v for k, v in config_kwargs.items() if v is not None}
        config = get_config(**config_kwargs)

        # Build ClientOptions and GuacdOptions from config and CLI
        client_options = ClientOptions(
            crypt=CryptConfig(
                cypher=crypt_cypher or "AES-256-CBC",
                key=config.secret_key,
            ),
            max_inactivity_time=inactivity_time,
        )
        guacd_options = GuacdOptions(
            host=config.guacd_host,
            port=config.guacd_port,
        )
        server = create_server(client_options, guacd_options)
        rich_print(
            "[bold green]Guapy server starting on [cyan]"
            f"{config.host}:{config.port}"
            "[/cyan]...[/bold green]"
        )
        logging.basicConfig(level=log_level.upper())
        import uvicorn

        uvicorn.run(
            server.app,
            host=config.host,
            port=config.port,
        )
    except Exception as e:
        console.print(f"[bold red]Error starting server:[/bold red] {e}", style="red")
        raise typer.Exit(code=1) from e


@app.command()
def show_config(
    config_file: str = typer.Option(
        None, help="Path to config file (default: config.json)"
    ),
) -> None:
    """Show the resolved server configuration."""
    try:
        config = get_config()
        console.print("[bold blue]Current Guapy server configuration:[/bold blue]")
        console.print(config)
    except Exception as e:
        console.print(f"[bold red]Error loading config:[/bold red] {e}", style="red")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
