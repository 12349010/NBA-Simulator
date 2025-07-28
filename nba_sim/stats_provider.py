# nba_sim/stats_provider.py

class StatsProvider:
    def __init__(self):
        # any setup (e.g. cache, API keys) would go here
        pass

    def get_stats(self, player_id: int, season: int) -> dict:
        """
        Placeholder: return a dict of baseline season stats for this player.
        In a real implementation you’d fetch from NBA Stats, sqlite, etc.
        """
        return {
            "points_per_game": 0.0,
            "assists_per_game": 0.0,
            "rebounds_per_game": 0.0,
            # …etc.
        }

# instantiate a single global provider
stats_provider = StatsProvider()
