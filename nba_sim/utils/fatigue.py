def fatigue_factor(minutes_played: float) -> float:
    """
    Simple linear fatigue: after 30 minutes, output drops 0.5 % per extra minute.
    """
    excess = max(0, minutes_played - 30)
    return 1.0 - 0.005 * excess
