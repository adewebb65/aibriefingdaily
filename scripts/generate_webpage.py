#!/usr/bin/env python3
"""
generate_webpage.py — Regenerate index.html from all daily briefing markdown files.

Scans state/daily/*.md, sorts by date descending, and writes a clean HTML page.
"""

import os
import re
import glob
from datetime import datetime


def parse_md_file(path):
    """Parse a daily briefing markdown file into structured sections."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    basename = os.path.basename(path)
    date_str = basename.replace(".md", "")

    stories = []
    # Split on ## headers (markdown level-2)
    parts = re.split(r"\n## ", content)
    for part in parts[1:]:  # skip preamble before first ##
        lines = part.strip().split("\n")
        if not lines:
            continue
        header = lines[0].strip()
        # Header format: "Story Title | Outlet | YYYY-MM-DD"
        header_parts = [p.strip() for p in header.split("|")]
        title = header_parts[0] if len(header_parts) > 0 else "Untitled"
        outlet = header_parts[1] if len(header_parts) > 1 else ""
        story_date = header_parts[2] if len(header_parts) > 2 else date_str

        # Body is everything after the header line, before the next --- separator
        body_lines = []
        for line in lines[1:]:
            if line.strip().startswith("---"):
                break
            body_lines.append(line)
        body = "\n".join(body_lines).strip()
        # Convert markdown bold to HTML
        body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
        # Convert markdown paragraphs to HTML
        body_html = ""
        for para in body.split("\n\n"):
            para = para.strip()
            if para:
                body_html += f"<p>{para}</p>\n"

        stories.append({
            "title": title,
            "outlet": outlet,
            "date": story_date,
            "body_html": body_html,
        })

    return {"date": date_str, "stories": stories}


def generate_html(briefings):
    """Generate the full HTML page."""
    briefings.sort(key=lambda x: x["date"], reverse=True)

    sections_html = ""
    for b in briefings:
        date_display = datetime.strptime(b["date"], "%Y-%m-%d").strftime("%A, %d %B %Y")
        stories_html = ""
        for i, story in enumerate(b["stories"], 1):
            stories_html += f"""
            <article class="story">
              <h3><span class="story-num">{i}.</span> {story["title"]}</h3>
              <div class="meta">{story["outlet"]} · {story["date"]}</div>
              <div class="body">{story["body_html"]}</div>
            </article>
            """
        sections_html += f"""
        <section class="day-briefing" id="{b["date"]}">
          <h2>{date_display}</h2>
          <div class="stories">
            {stories_html}
          </div>
        </section>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Briefing Daily</title>
  <style>
    :root {{
      --bg: #0d1117;
      --fg: #c9d1d9;
      --muted: #8b949e;
      --accent: #58a6ff;
      --border: #30363d;
      --card-bg: #161b22;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--fg);
      line-height: 1.6;
      padding: 2rem 1rem;
      max-width: 800px;
      margin: 0 auto;
    }}
    header {{
      text-align: center;
      padding-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 2rem;
    }}
    header h1 {{
      font-size: 2rem;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: -0.02em;
    }}
    header p {{
      color: var(--muted);
      margin-top: 0.5rem;
      font-size: 0.95rem;
    }}
    .day-briefing {{
      margin-bottom: 3rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid var(--border);
    }}
    .day-briefing:last-child {{
      border-bottom: none;
    }}
    .day-briefing h2 {{
      font-size: 1.25rem;
      color: var(--accent);
      margin-bottom: 1.25rem;
      font-weight: 600;
    }}
    .story {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      margin-bottom: 1rem;
    }}
    .story h3 {{
      font-size: 1.05rem;
      font-weight: 600;
      margin-bottom: 0.4rem;
      color: var(--fg);
    }}
    .story-num {{
      color: var(--accent);
      margin-right: 0.3rem;
    }}
    .meta {{
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .body p {{
      margin-bottom: 0.75rem;
      font-size: 0.95rem;
    }}
    .body p:last-child {{
      margin-bottom: 0;
    }}
    .body strong {{
      color: #e6edf3;
    }}
    footer {{
      text-align: center;
      color: var(--muted);
      font-size: 0.8rem;
      padding-top: 2rem;
      border-top: 1px solid var(--border);
    }}
  </style>
</head>
<body>
  <header>
    <h1>AI Briefing Daily</h1>
    <p>Curated AI technology news from globally recognised tier-one outlets.<br>
    New model releases, significant capabilities, milestones, and scandals — no routine updates.</p>
  </header>
  <main>
    {sections_html}
  </main>
  <footer>
    <p>Generated {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")} · ade@aibriefingdaily</p>
  </footer>
</body>
</html>
"""
    return html


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    daily_dir = os.path.join(base_dir, "state", "daily")
    output_path = os.path.join(base_dir, "index.html")

    md_files = glob.glob(os.path.join(daily_dir, "*.md"))
    briefings = [parse_md_file(f) for f in md_files]

    html = generate_html(briefings)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {output_path} from {len(briefings)} daily briefings.")


if __name__ == "__main__":
    main()
