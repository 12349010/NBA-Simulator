# nba_sim/calibration.py
import json
from nba_sim.main import play_game  # Added import for play_game
import nba_sim.weights as W


def calibrate(game_id: int, config: dict) -> dict:
    """
    Run a single simulation against provided game config to calibrate parameters.

    Args:
        game_id: ID of the real NBA game to calibrate against.
        config: Configuration dict with teams, rosters, etc.

    Returns:
        A dict containing simulation results and applied weight values.
    """
    # Perform the game simulation
    sim_output = play_game(game_id, config)

    # Retrieve saved calibration weights
    # Use W.load() instead of non-existent W.get_weights()
    weights_used = W.load()

    # Return combined calibration output
    return {
        'sim_output': sim_output,
        'weights_used': weights_used,
    }

# Optionally, you can add JSON I/O helpers if needed:

def save_calibration_results(path: str, results: dict):
    """
    Save calibration results to a JSON file.
    """
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
