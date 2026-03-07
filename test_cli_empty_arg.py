
import click
from click.testing import CliRunner

@click.command()
@click.option("--add", "add_tag", required=False)
@click.option("--remove", "remove_tag", required=False)
def tag(add_tag, remove_tag):
    if add_tag and remove_tag:
        click.echo("Error: Both provided")
        return
    if not add_tag and not remove_tag:
        click.echo("Error: None provided")
        return
    
    click.echo(f"Add: {add_tag!r}, Remove: {remove_tag!r}")

if __name__ == "__main__":
    runner = CliRunner()
    print("--- Test --add '' ---")
    result = runner.invoke(tag, ["--add", ""])
    print(f"Output: {result.output.strip()}")
