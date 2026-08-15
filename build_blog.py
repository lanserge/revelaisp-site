#!/usr/bin/env python3
"""Render the blog from markdown copies, into static pages.

The posts are WRITTEN somewhere else and COPIED here. That is deliberate:
a draft stays a draft, and only what was chosen for the site appears on
it. Re-run this after copying a new post into posts/.

Static output by intent — the same reason index.html has its CSS inline.
Nothing to build at request time, nothing to age, nothing between a commit
and a page load.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

HERE = Path(__file__).parent
POSTS = HERE / "posts"
OUT = HERE / "blog"

# The site's one stylesheet, kept identical to index.html so a post does
# not read like a different website.
STYLE = """
  :root {
    --bg: #ffffff; --fg: #1a1f24; --muted: #57606a; --line: #d0d7de;
    --card: #f6f8fa; --accent: #46a758; --code: #f6f8fa;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0d1117; --fg: #e6edf3; --muted: #8b949e; --line: #30363d;
      --card: #161b22; --accent: #3fb950; --code: #161b22;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--fg);
         font: 18px/1.7 -apple-system, "Segoe UI", Roboto, sans-serif; }
  nav { position: sticky; top: 0; z-index: 10; background: var(--bg);
        border-bottom: 1px solid var(--line); padding: .55rem clamp(1.2rem, 4vw, 3rem); }
  nav .inner { display: flex;
               align-items: center; justify-content: space-between; gap: 1rem; }
  nav a { text-decoration: none; font-size: .92rem; }
  nav .brand { display: flex; align-items: center; gap: .45rem;
               color: var(--fg); font-weight: 600; }
  nav .brand img { width: 20px; height: 20px; }
  nav .links a { margin-left: 1.1rem; color: var(--muted); }
  nav .links a:hover, nav .brand:hover { color: var(--accent); }
  nav .links a[aria-current] { color: var(--accent); }
  main { padding: 2rem clamp(1.2rem, 4vw, 3rem) 2rem; }
  .back { color: var(--muted); text-decoration: none; font-size: .9rem; }
  .back:hover { color: var(--accent); }
  h1 { font-size: 1.9rem; line-height: 1.25; margin: 1.2rem 0 .3rem; }
  h2 { font-size: 1.25rem; margin: 2.2rem 0 .6rem; }
  .date { color: var(--muted); font-size: .9rem; margin: 0 0 2rem; }
  p { margin: 1.1rem 0; }
  a { color: var(--accent); }
  ul.posts { list-style: none; padding: 0; }
  ul.posts li { border: 1px solid var(--line); border-radius: 8px;
                background: var(--card); margin-bottom: .7rem; }
  ul.posts a { display: block; padding: .8rem 1rem; text-decoration: none;
               color: var(--fg); }
  ul.posts a:hover { color: var(--accent); }
  ul.posts .date { margin: .2rem 0 0; }
  footer { padding: 1.2rem clamp(1.2rem, 4vw, 3rem);
           border-top: 1px solid var(--line); color: var(--muted);
           font-size: .85rem; }
  footer a { color: var(--accent); text-decoration: none; }
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="icon" href="/revela.svg" type="image/svg+xml">
<style>{style}</style>
</head>
<body>
<nav>
  <div class="inner">
    <a class="brand" href="/"><img src="/revela.svg" alt="">Revela ISP</a>
    <span class="links">
      <a href="/blog/" aria-current="page">Blog</a>
      <a href="https://github.com/lanserge/revela">GitHub</a>
      <a href="https://github.com/sponsors/lanserge">Sponsor</a>
    </span>
  </div>
</nav>
<main>
{body}
</main>
<footer>
  <a href="/">Revela ISP</a> — an image signal processor written in NumPy.
  More about me at <a href="https://serge.rabyking.com">serge.rabyking.com</a>.
</footer>
</body>
</html>
"""


def inline(text: str) -> str:
    """Escape, then restore the few inline forms these posts use."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def render(md: str) -> tuple[str, str]:
    """Markdown to HTML. Returns (title, body) — headings and paragraphs
    are all these posts use, and a converter that handles only what is
    present cannot mis-handle what is not."""
    title, chunks = "", []
    for block in re.split(r"\n\s*\n", md.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            title = block[2:].strip()
            chunks.append(f"<h1>{inline(title)}</h1>")
        elif block.startswith("## "):
            chunks.append(f"<h2>{inline(block[3:].strip())}</h2>")
        else:
            chunks.append(f"<p>{inline(block)}</p>")
    return title, "\n".join(chunks)


def date_of(name: str) -> str:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})-", name)
    if not m:
        return ""
    months = ("January February March April May June July August September "
              "October November December").split()
    return f"{int(m.group(3))} {months[int(m.group(2)) - 1]} {m.group(1)}"


def main() -> int:
    OUT.mkdir(exist_ok=True)
    entries = []
    for path in sorted(POSTS.glob("*.md"), reverse=True):
        title, body = render(path.read_text())
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
        when = date_of(path.name)
        head = f'<a class="back" href="/blog/">← Writing</a>'
        dateline = f'<p class="date">{when}</p>' if when else ""
        # the <h1> from the markdown carries the title; the date follows it
        body = body.replace("</h1>", "</h1>\n" + dateline, 1)
        (OUT / f"{slug}.html").write_text(PAGE.format(
            title=html.escape(title) + " — Revela ISP",
            description=html.escape(title),
            style=STYLE, body=head + "\n" + body))
        entries.append((when, title, f"/blog/{slug}.html"))

    items = "\n".join(
        f'  <li><a href="{url}"><strong>{html.escape(t)}</strong>'
        f'<p class="date">{w}</p></a></li>' for w, t, url in entries)
    (OUT / "index.html").write_text(PAGE.format(
        title="Writing — Revela ISP",
        description="Notes on building an open image signal processor.",
        style=STYLE,
        body=('<a class="back" href="/">← Revela ISP</a>\n<h1>Writing</h1>\n'
              f'<ul class="posts">\n{items}\n</ul>')))
    print(f"rendered {len(entries)} posts into blog/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
