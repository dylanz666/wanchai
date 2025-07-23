import re

# Read version from version.py
try:
    with open("version.py", encoding="utf-8") as f:
        m = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", f.read())
        version = m.group(1) if m else "1.0.0"
except Exception:
    version = "1.0.0"

web_version = f"{version}"
web_title = f"WanChai INI File Editor(v{web_version})"

# Read index.html
with open("index.html", encoding="utf-8") as f:
    html = f.read()

# Replace <title>...</title>
html = re.sub(
    r"<title>.*?</title>", f"<title>{web_title}</title>", html, flags=re.DOTALL
)
# Replace <h2 id="app-title" ...>...</h2>
html = re.sub(
    r'(<h2[^>]*id=["\']app-title["\'][^>]*>)(.*?)(</h2>)',
    rf"\1{web_title}\3",
    html,
    flags=re.DOTALL,
)

# Write back
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"index.html updated with version: {web_title}")
