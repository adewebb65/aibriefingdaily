#!/usr/bin/env python3
"""
Generate index.html from all state/daily/*.md files.
Shows today's briefing prominently and links to archive summaries.
"""

import os
import glob
import re
from datetime import datetime

DAILY_DIR = os.path.join("state", "daily")
INDEX_PATH = "index.html"

def parse_markdown_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    basename = os.path.basename(filepath)
    date_str = basename.replace('.md', '')
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else f"Daily Briefing — {date_str}"
    stories = []
    story_pattern = r'##\s*(?:\d+\.\s*)?(.+?)\s*\|\s*(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\n+(?:\*\*Summary:\*\*|Summary:)(.+?)\n+(?:\*\*Why it matters:\*\*|Why it matters:)(.+?)(?=\n+---|\n+##\s*(?:\d+\.|[^#])|\Z)'
    for match in re.finditer(story_pattern, content, re.DOTALL):
        stories.append({
            'title': match.group(1).strip(),
            'outlet': match.group(2).strip(),
            'date': match.group(3).strip(),
            'summary': match.group(4).strip(),
            'why': match.group(5).strip()
        })
    return {
        'date': date_str,
        'title': title,
        'stories': stories,
        'raw': content
    }

def generate_html(briefings):
    today = datetime.now().strftime("%Y-%m-%d")
    briefings.sort(key=lambda x: x['date'], reverse=True)
    today_briefing = None
    archives = []
    for b in briefings:
        if b['date'] == today:
            today_briefing = b
        else:
            archives.append(b)
    if not today_briefing and briefings:
        today_briefing = briefings[0]
        archives = briefings[1:]
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>AI Technology Daily Briefing</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --muted: #94a3b8; --accent: #3b82f6; --border: #334155; --success: #22c55e; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; padding: 2rem 1rem; }
        .container { max-width: 900px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 2rem; }
        header h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
        header p { color: var(--muted); }
        .today { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }
        .today h2 { color: var(--accent); font-size: 1.3rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }
        .story { margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border); }
        .story:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .story h3 { font-size: 1.1rem; margin-bottom: 0.5rem; color: var(--text); }
        .story .meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 0.5rem; }
        .story .summary { color: var(--text); margin-bottom: 0.5rem; }
        .story .why { color: var(--muted); font-size: 0.9rem; border-left: 3px solid var(--accent); padding-left: 0.75rem; }
        .why-label { color: var(--accent); font-weight: 600; }
        .archives { margin-top: 2rem; }
        .archives h2 { font-size: 1.2rem; margin-bottom: 1rem; color: var(--accent); }
        .archive-list { display: grid; gap: 0.5rem; }
        .archive-item { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 1rem; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: var(--text); transition: background 0.2s; }
        .archive-item:hover { background: #283548; }
        .archive-item .date { font-weight: 600; }
        .archive-item .count { color: var(--muted); font-size: 0.85rem; }
        .archive-detail { display: none; padding: 0.75rem 1rem; background: #0f172a; border-radius: 0 0 8px 8px; border-top: 1px solid var(--border); }
        .archive-detail.active { display: block; }
        .archive-detail ul { list-style: none; padding: 0; margin: 0; }
        .archive-detail li { padding: 0.35rem 0; font-size: 0.9rem; color: var(--muted); border-bottom: 1px solid #1e293b; }
        .archive-detail li:last-child { border-bottom: none; }
        .archive-detail li a { color: var(--accent); text-decoration: none; }
        .archive-detail li a:hover { text-decoration: underline; }
        .archive-row { cursor: pointer; }
        .archive-toggle { color: var(--muted); font-size: 0.8rem; margin-left: 0.5rem; }
        footer { text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.85rem; }
        .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem; }
        .badge-today { background: var(--success); color: #064e3b; }
        @media (max-width: 600px) { body { padding: 1rem 0.75rem; } header h1 { font-size: 1.4rem; } .today { padding: 1rem; } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 AI Technology Daily Briefing</h1>
            <p>Curated for Ade — Tier-1 sources only</p>
        </header>
""")
    if today_briefing:
        is_today = today_briefing['date'] == today
        badge = '<span class="badge badge-today">TODAY</span>' if is_today else ''
        html_parts.append(f'<section class="today"><h2>📰 {today_briefing["date"]} {badge}</h2>')
        for i, story in enumerate(today_briefing['stories'], 1):
            html_parts.append(f"""
            <div class="story">
                <h3>{i}. {story['title']}</h3>
                <div class="meta">{story['outlet']} | {story['date']}</div>
                <div class="summary">{story['summary']}</div>
                <div class="why"><span class="why-label">Why it matters:</span> {story['why']}</div>
            </div>
            """)
        html_parts.append('</section>')

    if archives:
        html_parts.append("""
        <section class="archives">
            <h2>📁 Archive</h2>
            <div class="archive-list">
        """)
        for b in archives:
            count = len(b['stories'])
            story_titles = [s['title'] for s in b['stories']]
            story_list_html = ''.join([f'<li><a href="state/daily/{b["date"]}.md">{t}</a></li>' for t in story_titles])
            html_parts.append(f"""
                <div class="archive-wrap">
                    <div class="archive-item archive-row" onclick="this.nextElementSibling.classList.toggle('active'); this.querySelector('.archive-toggle').textContent = this.nextElementSibling.classList.contains('active') ? '▲' : '▼';">
                        <span class="date">{b['date']}</span>
                        <span class="count">{count} stories <span class="archive-toggle">▼</span></span>
                    </div>
                    <div class="archive-detail">
                        <ul>
                            {story_list_html}
                        </ul>
                    </div>
                </div>
            """)
        html_parts.append("""
            </div>
        </section>
        """)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    html_parts.append(f"""
        <footer>
            <p>Last updated: {now_str}</p>
            <p style="margin-top:0.5rem;font-size:0.75rem;">Auto-generated daily at 06:15 UTC</p>
        </footer>
    </div>
</body>
</html>
    """)
    return "\n".join(html_parts)

def main():
    files = glob.glob(os.path.join(DAILY_DIR, "*.md"))
    if not files:
        print(f"No markdown files found in {DAILY_DIR}")
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>AI Briefing</title></head><body><h1>No briefings yet</h1></body></html>')
        return
    briefings = []
    for filepath in files:
        try:
            briefing = parse_markdown_file(filepath)
            briefings.append(briefing)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
    html = generate_html(briefings)
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated {INDEX_PATH} with {len(briefings)} briefing(s)")
    if briefings:
        dates = [b['date'] for b in briefings]
        print(f"Date range: {min(dates)} to {max(dates)}")

if __name__ == "__main__":
    main()
