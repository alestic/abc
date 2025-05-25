"""Integration tests for abc-cli functionality."""

import pytest
import subprocess
import sys
import os
from unittest.mock import patch, Mock
from pathlib import Path
from abc_cli import abc_generate
from abc_cli.abc_generate import main, get_config_file, process_generated_command
from importlib import metadata

@pytest.mark.integration
class TestCommandGeneration:
    """Test the full command generation flow."""
    
    def test_basic_command_generation(self, isolated_environment, mock_config_file, mock_provider_entry_point, monkeypatch):
        """Test generating a simple command."""
        # Mock the entry points discovery
        with patch.object(metadata, 'entry_points') as mock_entry_points:
            mock_entry_points.return_value = {'abc.llm_providers': [mock_provider_entry_point]}
            
            # Mock sys.argv
            test_args = ['abc_generate', 'list', 'files', 'in', 'current', 'directory']
            with patch.object(sys, 'argv', test_args):
                # Capture stdout
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    exit_code = main()
                
                output = f.getvalue().strip()
                
                assert exit_code == 0
                assert output == "ls -la"
    
    def test_dangerous_command_marking(self, isolated_environment, mock_config_file, mock_provider_entry_point):
        """Test that dangerous commands are properly marked."""
        # Create a provider that returns a dangerous command
        dangerous_provider = Mock()
        dangerous_provider.get_config_schema.return_value = {
            'required': ['provider', 'api_key'],
            'properties': {'provider': {'enum': ['mock_provider']}, 'api_key': {'type': 'string'}}
        }
        dangerous_provider.generate_command.return_value = "rm -rf /\n##DANGERLEVEL=2## Extremely dangerous"
        
        mock_provider_entry_point.load.return_value = lambda config: dangerous_provider
        
        with patch.object(metadata, 'entry_points') as mock_entry_points:
            mock_entry_points.return_value = {'abc.llm_providers': [mock_provider_entry_point]}
            
            test_args = ['abc_generate', 'delete', 'everything']
            with patch.object(sys, 'argv', test_args):
                import io
                from contextlib import redirect_stdout, redirect_stderr
                
                f_out = io.StringIO()
                f_err = io.StringIO()
                with redirect_stdout(f_out), redirect_stderr(f_err):
                    exit_code = main()
                
                output = f_out.getvalue().strip()
                error = f_err.getvalue()
                
                assert exit_code == 0
                assert output == "#DANGEROUS# rm -rf /"
                assert "Warning: This command is potentially dangerous" in error



    def test_no_description_error(self, isolated_environment, mock_config_file, mock_provider_entry_point):
        """Test error when no description is provided."""
        with patch.object(metadata, 'entry_points') as mock_entry_points:
            mock_entry_points.return_value = {'abc.llm_providers': [mock_provider_entry_point]}
            
            test_args = ['abc_generate']
            with patch.object(sys, 'argv', test_args):
                # Capture log output
                import logging
                import io
                
                # Set up logging capture
                log_capture = io.StringIO()
                handler = logging.StreamHandler(log_capture)
                handler.setLevel(logging.ERROR)
                logger = logging.getLogger()
                logger.addHandler(handler)
                
                try:
                    exit_code = main()
                    
                    assert exit_code == 1
                    log_output = log_capture.getvalue()
                    assert "No description provided" in log_output
                finally:
                    logger.removeHandler(handler)


@pytest.mark.integration
class TestConfigHandling:
    """Test configuration file handling."""
    
    def test_xdg_config_path(self, monkeypatch, tmp_path):
        """Test XDG config path is used correctly when it exists."""
        # Create a fake home to avoid real config files
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        
        # Create custom XDG config directory
        custom_config = tmp_path / "custom" / "config" / "abc"
        custom_config.mkdir(parents=True)
        config_file = custom_config / "config"
        config_file.touch()
        
        monkeypatch.setenv('HOME', str(fake_home))
        monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / "custom" / "config"))
        monkeypatch.delenv('ABC_CONFIG', raising=False)
        
        config_path = get_config_file()
        assert config_path == str(config_file)
    
    def test_config_override_env(self, monkeypatch):
        """Test ABC_CONFIG environment variable override."""
        monkeypatch.setenv('ABC_CONFIG', '/custom/abc.conf')
        
        config_path = get_config_file()
        assert config_path == '/custom/abc.conf'
    
    def test_legacy_config_warning(self, tmp_path, monkeypatch, capsys):
        """Test warning when both XDG and legacy configs exist."""
        # Set up paths
        xdg_dir = tmp_path / ".config" / "abc"
        xdg_dir.mkdir(parents=True)
        xdg_config = xdg_dir / "config"
        xdg_config.touch()
        
        legacy_config = tmp_path / ".abc.conf"
        legacy_config.touch()
        
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.delenv('XDG_CONFIG_HOME', raising=False)
        monkeypatch.delenv('ABC_CONFIG', raising=False)
        
        config_path = get_config_file()
        
        captured = capsys.readouterr()
        assert "Warning: Found both XDG config and legacy config" in captured.err
        assert config_path == str(xdg_config)


