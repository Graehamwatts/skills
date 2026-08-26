#!/usr/bin/env python3
"""Character budget checker for listing remarks.

Usage:
    python charcount.py <file> [limit]
    echo "text" | python charcount.py - [limit]

Default limit is 1300 (MLSListings public remarks).

Prints the total count, headroom against the limit, and a per-sentence
cost table so a trim pass targets the expensive sentences instead of
guessing. Exit code 1 if over the limit.
"""
import io
import re
import sys

DEFAULT_LIMIT = 1300


def sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    src = sys.argv[1]
    if src in ('-h', '--help', 'help'):
        print(__doc__)
        return 0
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_LIMIT

    if src == '-':
        text = sys.stdin.read()
    else:
        text = io.open(src, encoding='utf-8').read()

    # MLS fields are single-paragraph; collapse whitespace the way the
    # field will, so the count matches what the MLS actually stores.
    text = re.sub(r'\s+', ' ', text).strip()
    n = len(text)

    print('count : %d' % n)
    print('limit : %d' % limit)
    if n > limit:
        print('STATUS: OVER by %d characters. Trim before delivering.' % (n - limit))
    elif n < int(limit * 0.90):
        print('STATUS: UNDER-USED. %d characters unspent (below 90%% of limit).'
              % (limit - n))
        print('        Add feature nouns before delivering.')
    else:
        print('STATUS: OK. %d characters of headroom.' % (limit - n))

    print('')
    print('per-sentence cost (largest first):')
    ranked = sorted(sentences(text), key=len, reverse=True)
    for s in ranked:
        preview = s if len(s) <= 70 else s[:67] + '...'
        print('  %4d  %s' % (len(s), preview))

    return 1 if n > limit else 0


if __name__ == '__main__':
    sys.exit(main())
