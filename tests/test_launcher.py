from unittest.mock import patch, MagicMock

from windrose.launcher.game import launch_game


def test_launch_game_calls_popen():
    mock_proc = MagicMock()
    with patch("windrose.launcher.game.subprocess.Popen", return_value=mock_proc) as mock_popen:
        proc = launch_game("/path/to/Windrose.exe")

    mock_popen.assert_called_once_with("/path/to/Windrose.exe")
    assert proc is mock_proc
