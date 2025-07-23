def age_multiplier(age: int) -> float:
    """
    Performance peaks ~28, gentle rise from 18 → 22, slow decline after 28.
    Returns a multiplier in [0.65, 1.0].
    """
    if age <= 22:
        return 0.85 + 0.03 * (age - 18)
    if age <= 28:
        return 1.0
    return max(0.65, 1.0 - 0.035 * (age - 28))
