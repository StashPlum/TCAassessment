"""Versioned local cumulative gates; neither version grants CAT standing."""
POLICY = 'draft-v1'
ADVISORY_POLICY = 'advisory-v2'
LEVELS = ((5, 'Certified'), (8, 'Advanced'), (10, 'Showcase'))

def pass_codes(policy_version):
    if policy_version == POLICY: return frozenset({'Y'})
    if policy_version == ADVISORY_POLICY: return frozenset({'Y','A'})
    return frozenset()  # unknown policy never grants a local gate

def category_result(responses, policy_version=POLICY):
    """responses maps position 1..10 to Y/N/A/blank; missing is unanswered."""
    earned = None
    blockers = {}
    for threshold, name in LEVELS:
        missing = [i for i in range(1, threshold + 1) if responses.get(i) not in pass_codes(policy_version)]
        blockers[name] = missing
        if not missing:
            earned = name
    return {'policy': policy_version, 'approved_policy': False, 'earned': earned, 'blockers': blockers}
