import typer
from cli.commands.plan import app as plan_app

app = typer.Typer()

app.add_typer(plan_app)

if __name__ == "__main__":
    app()
