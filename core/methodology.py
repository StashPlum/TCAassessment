"""Methodological event type (A4/A3/Business Process) rules taken from the Global Kaizen template.

Input view (small/medium/extensive) and report paper (A3/A4 PDF) are separate choices and never
derive from these rules. Only differences that the immutable template states are enforced; every
other difference is listed as an open CEVA interpretation instead of being guessed.
"""

RULES = {
    'A4': {
        'label': 'A4 Kaizen',
        'cause_analysis': 'optional',
        'upload_type': 'A4 Kaizen',
        'upload_category': 'Standard',
        'summary': 'Cause analysis / investigation is optional (PLAN!B69). Reported as a standard A4 Kaizen.',
    },
    'A3': {
        'label': 'A3 Kaizen',
        'cause_analysis': 'required',
        'upload_type': 'A3 Kaizen',
        'upload_category': 'Standard',
        'summary': 'Cause analysis / investigation is part of the event (PLAN!B69 is optional only for A4). Reported as a standard A3 Kaizen.',
    },
    'BP': {
        'label': 'Business Process Kaizen (BPK)',
        'cause_analysis': 'required',
        'upload_type': 'A3 Kaizen',
        'upload_category': 'Business Process Kaizen (BPK)',
        'summary': 'Cause analysis / investigation is part of the event (PLAN!B69). The legacy upload reports it as an A3 Kaizen with category BPK (DL_UPLOAD!C22/F22).',
    },
}

SOURCES = [
    ('PLAN!B69', 'Cause analysis / investigation heading marked "Optional for A4".'),
    ('DROP_DOWNS!G4:G6', 'Kaizen type list: A4 Kaizen, A3 Kaizen, Business Process Kaizen (BPK).'),
    ('DL_UPLOAD!C22, F22', 'Upload mapping: A4/A3 report category Standard; BPK is reported as type A3 Kaizen.'),
]

OPEN_INTERPRETATIONS = [
    'The template marks cause analysis optional only for A4. Treating it as required for A3 and BPK is the textual reading; CEVA confirmation is open.',
    'No source rule ties A4 or A3 events to a report paper size. The PDF paper (A3 or A4) is a separate download choice.',
    'No source rule ties A4/A3/BPK to Small, Medium or Extensive input views. No Small=A4 mapping is applied.',
    'Further A3/BPK mandatory fields, team size, duration or approval routes need the missing Kaizen User Guide.',
]


def rules_for(profile):
    return RULES.get(profile, RULES['A4'])


def cause_analysis_required(event):
    return rules_for(event.profile)['cause_analysis'] == 'required'
