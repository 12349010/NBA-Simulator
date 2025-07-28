import pandas as pd


def play_game(home_name: str,
              away_name: str,
              season: int,
              home_players: list[str],
              away_players: list[str],
              speed: float = 1.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Stub implementation of play_game. Returns empty box score and play-by-play DataFrames.
    Replace with full simulation logic when ready.
    """
    # Create an empty box score DataFrame
    box_columns = ['player', 'team', 'points', 'rebounds', 'assists']
    box_score_df = pd.DataFrame(columns=box_columns)

    # Create an empty play-by-play DataFrame
    pbp_columns = ['time', 'description', 'home_score', 'away_score']
    pbp_df = pd.DataFrame(columns=pbp_columns)

    return box_score_df, pbp_df
