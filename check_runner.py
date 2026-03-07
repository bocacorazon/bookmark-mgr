from click.testing import CliRunner
import sys, click

@click.command()
def test():
    click.echo("out")
    click.echo("err", err=True)

runner = CliRunner()
res = runner.invoke(test)
print(f"mix={getattr(runner, 'mix_stderr', 'unknown')}, output={res.output!r}, stdout={res.stdout!r}, stderr={res.stderr!r}")

runner2 = CliRunner(mix_stderr=False)
res2 = runner2.invoke(test)
print(f"mix=False, output={res2.output!r}, stdout={res2.stdout!r}, stderr={res2.stderr!r}")
