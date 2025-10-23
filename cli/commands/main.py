import typer
from cli.commands.plan import app as plan_command
from cli.commands.backup import app as backup_command

app = typer.Typer()

app.add_typer(plan_command)
app.add_typer(backup_command)

if __name__ == "__main__":
    app()
