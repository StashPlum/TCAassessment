"""Presentation helpers. Official wording is never changed: lettered lines are only styled, not rewritten."""
import re
from django import template

register = template.Library()
LETTER = re.compile(r'^(\s*[A-Z]\.\))(.*)$', re.S)


@register.filter
def requirement_blocks(text):
    """Split exact requirement text into paragraphs, lettered sub-requirements and spacer gaps for display."""
    blocks = []
    for line in (text or '').split('\n'):
        if not line.strip():
            if blocks and blocks[-1]['kind'] != 'gap': blocks.append({'kind': 'gap'})
            continue
        match = LETTER.match(line)
        if match: blocks.append({'kind': 'item', 'label': match.group(1), 'text': match.group(2)})
        elif blocks and blocks[-1]['kind'] == 'item': blocks[-1].setdefault('more', []).append(line)
        else: blocks.append({'kind': 'para', 'text': line})
    return blocks


@register.filter
def qid(code):
    """QuestionID shown to people; the internal variant suffix (~n) is never displayed."""
    return str(code or '').split('~')[0]


@register.filter
def answer_label(code):
    return {'Y': 'Yes', 'A': 'Advisory', 'N': 'No'}.get(code or '', 'Not answered')


@register.filter
def answer_state(code):
    return {'Y': 'yes', 'A': 'advisory', 'N': 'no'}.get(code or '', 'unanswered')


@register.filter
def band(level_code):
    return {'C': 'Certified', 'B': 'Advanced', 'A': 'Showcase'}.get(level_code, '')
