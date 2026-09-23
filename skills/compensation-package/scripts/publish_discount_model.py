"""Publish the discount-model page as an unlisted page on the Online Content site.

- Puts it under an unguessable folder so it can't be found by swapping 'Standard' or
  'Premium' in the sibling URLs.
- Commits ONLY that one file, pushes with the PAT passed as an HTTP header (never in a
  URL, never printed), and masks the token in any output just in case.
"""
import base64, os, secrets, shutil, subprocess, sys

OC = r"C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\Online Content"
SKILLS = r"C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\Skills"
built = sys.argv[1]
slug_file = sys.argv[2]

pat = open(os.path.join(OC, "github-token.txt"), encoding="utf-8").read().strip()
b64 = base64.b64encode(("Graehamwatts:" + pat).encode()).decode()


def mask(s):
    return s.replace(pat, "***").replace(b64, "***")


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return r.returncode, mask((r.stdout or "") + (r.stderr or ""))


# reuse the slug if this is a republish, otherwise mint one
if os.path.exists(slug_file):
    slug = open(slug_file).read().strip()
else:
    slug = secrets.token_hex(6)
    open(slug_file, "w").write(slug)

rel = "compensation/%s/Compensation-Package-Discount-Model.html" % slug
dst = os.path.join(OC, *rel.split("/"))
os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copyfile(built, dst)

# brand tripwire on just this folder
rc, out = run([sys.executable, os.path.join(SKILLS, "scripts", "verify_brand_identity.py"), "--path", os.path.dirname(dst)])
print(out.strip()[-400:])
if rc != 0:
    sys.exit("brand check failed, not pushing")

git = ["git", "-C", OC, "-c", "credential.helper=", "-c", "http.extraheader=Authorization: Basic " + b64]

rc, out = run(git + ["pull", "--quiet", "--ff-only", "origin", "main"])
print("pull:", rc, out.strip()[-300:])

rc, out = run(["git", "-C", OC, "add", rel])
print("add:", rc, out.strip())

msg = (
    "Compensation package: add unlisted Discount Model page (relationship rate, 3+ transactions)\n\n"
    "Not linked from Standard or Premium and marked noindex. Shared by direct link only.\n\n"
    "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
)
rc, out = run(["git", "-C", OC, "commit", "-q", "-m", msg, "--", rel])
print("commit:", rc, out.strip()[-300:])

rc, out = run(git + ["push", "origin", "HEAD:main"])
print("push:", rc, out.strip()[-400:])
if rc != 0:
    sys.exit("push failed")

print("URL: https://graehamwatts.github.io/online-content/" + rel)
