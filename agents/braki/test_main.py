"""Tests for the Braki agent."""

from agents.braki import main

def test_run(capsys):
    main.run()
    captured = capsys.readouterr()
    assert "Braki agent starting" in captured.out
