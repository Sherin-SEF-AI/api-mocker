
from typer.testing import CliRunner
from api_mocker.cli import app
from unittest.mock import patch, MagicMock
import os
import shutil
import pytest

runner = CliRunner()

@pytest.fixture
def clean_cwd(tmp_path):
    # Run tests in a temp directory
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)

def test_start_help():
    result = runner.invoke(app, ["start", "--help"])
    assert result.exit_code == 0
    assert "Start the API mock server" in result.stdout

def test_init_command(clean_cwd):
    result = runner.invoke(app, ["init", "--name", "test-project"])
    assert result.exit_code == 0
    assert "Project created" in result.stdout
    assert os.path.exists("test-project/config/api-mock.yaml")

def test_export_command(clean_cwd):
    # First create a dummy config
    runner.invoke(app, ["init", "--name", "test-project"])
    config_path = "test-project/config/api-mock.yaml"
    
    result = runner.invoke(app, ["export", config_path, "--output", "spec.yaml"])
    assert result.exit_code == 0
    assert os.path.exists("spec.yaml")

def test_import_command_missing_file():
    result = runner.invoke(app, ["import-spec", "non_existent_file.yaml"])
    assert result.exit_code == 1
    assert "File not found" in result.stdout

@patch("api_mocker.cli.MockServer")
def test_start_server(mock_server_cls):
    mock_instance = MagicMock()
    mock_server_cls.return_value = mock_instance
    
    result = runner.invoke(app, ["start", "--port", "9000"])
    
    assert result.exit_code == 0
    mock_server_cls.assert_called_once()
    mock_instance.start.assert_called_with(host="127.0.0.1", port=9000)

def test_list_routes(clean_cwd):
    # Create config file
    runner.invoke(app, ["init", "--name", "test-project"])
    config_path = "test-project/config/api-mock.yaml"
    
    result = runner.invoke(app, ["list-routes", "--config", config_path])
    assert result.exit_code == 0
    assert "Configured Routes" in result.stdout
    assert "GET" in result.stdout
    assert "/api/users" in result.stdout
