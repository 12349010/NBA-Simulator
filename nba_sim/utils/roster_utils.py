from collections import defaultdict

def assign_lineup(players):
    """
    Given a list of Player objects (with .position and .height attributes),
    return (starters, bench).
    Logic:
      • Pick 1 C (or tallest if no “C”)
      • Pick 2 wings (SF/PF)
      • Pick 2 guards (PG/SG)
      • Fallback by height if a slot can’t be filled.
    """
    by_pos = defaultdict(list)
    for p in players:
        by_pos[p.position or ""][].append(p)

    # helper: sort descending by height (inches)
    sort_height = lambda lst: sorted(lst, key=lambda x: x.height or 0, reverse=True)

    starters = []
    # center
    cs = sort_height(by_pos.get("C", []))
    if cs:
        starters.append(cs.pop(0))
    # wings
    wings = sort_height(by_pos.get("SF",[]) + by_pos.get("PF",[]))
    starters.extend(wings[:2])
    # guards
    guards = sort_height(by_pos.get("PG",[]) + by_pos.get("SG",[]))
    starters.extend(guards[:2])

    # if we’re still under 5 (missing positions), fill by tallest remaining
    remaining = [p for p in players if p not in starters]
    starters += sort_height(remaining)[: max(0, 5 - len(starters))]

    # bench is everyone else
    bench = [p for p in players if p not in starters]
    return starters, bench
