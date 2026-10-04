"""Deterministic, unapproved cumulative rule for local exploration only."""
POLICY = 'draft-v1'
LEVELS = ((5, 'Certified'), (8, 'Advanced'), (10, 'Showcase'))

def category_result(responses):
    """responses maps position 1..10 to Y/N/A/blank; missing is unanswered."""
    earned = None
    blockers = {}
    for threshold, name in LEVELS:
        missing = [i for i in range(1, threshold + 1) if responses.get(i) != 'Y']
        blockers[name] = missing
        if not missing:
            earned = name
    return {'policy': POLICY, 'approved_policy': False, 'earned': earned, 'blockers': blockers}
