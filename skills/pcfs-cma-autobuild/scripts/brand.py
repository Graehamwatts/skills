"""Brand values for generated output.

Source of truth is skills/shared-references/identity.json. When this skill is installed on its own (a teammate's
computer), that file is not beside it, so a small snapshot in assets/ is used instead. Never type brand values
into a script or a report by hand."""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))
_LIVE = os.path.join(HERE, '..', '..', 'shared-references', 'identity.json')
_SNAP = os.path.join(HERE, '..', 'assets', 'identity_snapshot.json')


def load_identity():
    if os.path.exists(_LIVE):
        i = json.load(open(_LIVE, encoding='utf-8'))['identity']
    else:
        i = json.load(open(_SNAP, encoding='utf-8'))
    return {k: i[k] for k in ('name', 'title', 'dre', 'phone', 'email', 'website', 'brand_line')}


ID = load_identity()
