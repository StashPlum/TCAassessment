"""Beginner chooser: start from the question a team is asking, not from a method name.

Plain local guidance; each need points to registered methods in the order a first-time team would try them.
"""
NEEDS = (
    ('vague', 'The problem is still vague', 'Plan', 'Write down what happens, where and how often before looking for causes.', ('5w2h', 'gemba', 'is-not')),
    ('cause', 'We do not know why it happens', 'Plan', 'Collect possible causes first, then test the most likely one with data.', ('ishikawa', '5whys', 'is-not')),
    ('biggest', 'We do not know which problem matters most', 'Plan', 'Count occurrences for a fixed period, then rank them.', ('check-sheet', 'pareto', 'stratification')),
    ('flow', 'We want to see where time or walking is lost', 'Plan', 'Follow one order or pallet through the real process and mark waiting and movement.', ('flowchart', 'spaghetti', 'waste')),
    ('choose', 'We have ideas and must pick one', 'Do', 'List the options, then compare effort and expected effect with the team.', ('brainstorm', 'impact-effort', 'decision-matrix')),
    ('mistakes', 'We want to stop mistakes from happening', 'Do', 'Look at where an error can occur and make the right way the easy way.', ('poka-yoke', 'fmea', '5s')),
    ('worked', 'We want to know if the change worked', 'Check', 'Measure the same thing, the same way, before and after the change.', ('run-chart', 'check-sheet', 'histogram')),
    ('keep', 'We want the improvement to last', 'Act', 'Describe the new way of working and agree who checks it and how often.', ('standard-work', 'control-plan', 'visual-management')),
)


def needs(registry):
    """Needs with their method specs; a key missing from the registry is skipped rather than shown broken."""
    return [{'key': key, 'question': question, 'stage': stage, 'tip': tip,
             'methods': [registry[k] for k in keys if k in registry]} for key, question, stage, tip, keys in NEEDS]
