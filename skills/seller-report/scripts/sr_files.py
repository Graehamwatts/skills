# -*- coding: utf-8 -*-
"""sr_files: where a listing's working files live, and how they are read and written.

Shared by intake_sheet.py, curation_tools.py, build_ledger.py and snapshot_issue.py.

    listing_paths(folder)     the standard file names inside one listing folder
    load_json / save_json     UTF-8, one-space indent, written through a temp file so a crash leaves the old copy
    refuse_inside_repo(path)  private data is never written inside a git repo (the skills folder publishes)
    sha256_file / sha256_text
    issue_dir(folder, n)      issues\\NN

Standard library only. No real client data belongs in this file.
"""
import hashlib
import json
import os
import sys

PRIVATE_NAMES = ("listing.json", "raw.json", "curation.json", "events.json", "ledger.json", "market.json", "marketing.json",
                 "notes_for_operator.json")


def listing_paths(folder):
    """The files of one listing folder (<reports>\\seller-reports\\<slug>)."""
    f = os.path.abspath(folder)
    out = dict((name[:-5], os.path.join(f, name)) for name in PRIVATE_NAMES)
    out.update(folder=f, issues=os.path.join(f, "issues"), work=os.path.join(f, "work"))
    return out


def issue_dir(folder, number):
    return os.path.join(os.path.abspath(folder), "issues", "%02d" % int(number))


def load_json(path, default=None):
    """The parsed file. A missing file gives `default` when one is passed, else raises."""
    if not os.path.exists(path):
        if default is not None:
            return default
        raise SystemExit("missing file: %s" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dumps(data):
    return json.dumps(data, indent=1, ensure_ascii=False) + "\n"


def save_json(path, data, private=True):
    """Writes JSON as UTF-8 with LF line ends. With private=True the write is refused inside a git repo."""
    path = os.path.abspath(path)
    if private:
        refuse_inside_repo(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(data))
    os.replace(tmp, path)
    return path


def save_text(path, text, private=True):
    path = os.path.abspath(path)
    if private:
        refuse_inside_repo(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)
    return path


def git_root(path):
    """The folder that holds .git above this path, or None."""
    p = os.path.abspath(path)
    while True:
        if os.path.exists(os.path.join(p, ".git")):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            return None
        p = parent


def refuse_inside_repo(path):
    """Real names, notes and feedback never go into a git repo. The skills folder publishes to GitHub, so a
    private file written there would leak on the next push. Tests write to a temp folder."""
    root = git_root(os.path.dirname(os.path.abspath(path)))
    if root:
        raise SystemExit("refusing to write private data inside a git repo (%s): %s\n"
                         "Listing data belongs under <reports>\\seller-reports\\<slug>." % (root, path))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def say(*parts):
    """Prints to stdout without tripping on a console that is not UTF-8."""
    text = " ".join(str(p) for p in parts)
    try:
        print(text)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        print(text.encode(enc, "replace").decode(enc))


def shout(*parts):
    """A warning the operator must see: stderr, with a marker that is easy to find in a long log."""
    text = "ATTENTION: " + " ".join(str(p) for p in parts)
    try:
        sys.stderr.write(text + "\n")
    except UnicodeEncodeError:
        sys.stderr.write(text.encode("ascii", "replace").decode("ascii") + "\n")
