import typer
from typing import Annotated

app = typer.Typer()

@app.command()
def backup():
    print("Hello from backup command!")
