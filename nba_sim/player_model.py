from dataclasses import dataclass, field

@dataclass
class Player:
    """
    Represents an NBA player in the simulation with basic stats tracking.
    """
    name: str
    season: int
    position: str = None
    height: float = None
    weight: float = None
    # stat tracking dictionary
    g: dict = field(default_factory=lambda: {
        'minutes': 0,
        'points': 0,
        'rebounds': 0,
        'assists': 0,
        'field_goals': 0,
        'three_points': 0,
        'two_points': 0
    })
    minutes_so_far: float = 0.0

    def shot(self, made: bool, is3: bool):
        """
        Record a shot attempt and update scoring stats.
        """
        self.g['field_goals'] += 1
        if made:
            pts = 3 if is3 else 2
            self.g['points'] += pts
            if is3:
                self.g['three_points'] += 1
            else:
                self.g['two_points'] += 1

    def misc(self):
        """
        Placeholder for other stats like rebounds, assists, turnovers, etc.
        Extend this method to simulate these events.
        """
        pass
