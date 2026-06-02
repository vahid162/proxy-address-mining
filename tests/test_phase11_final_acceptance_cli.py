from typer.testing import CliRunner
from mpf.interfaces.cli import app
def test_cli_registered(): assert 'phase11-final-acceptance' in CliRunner().invoke(app,['production','--help']).stdout
