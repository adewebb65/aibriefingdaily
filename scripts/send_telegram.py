#!/usr/bin/env python3
"""
send_telegram.py — Send a markdown briefing to a Telegram chat.

Usage:
    python scripts/send_telegram.py state/daily/YYYY-MM-DD.md

Environment:
    TELEGRAM_BOT_TOKEN  — Bot token from @BotFather
    TELEGRAM_CHAT_ID    — Target chat ID (user or group)
"""

import os
import sys
import json
import urllib.request
import urllib.error


def send_message(token, chat_id, text, parse_mode="Markdown"):
    """Send a text message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def split_message(text, max_length=4096):
    """Split text into chunks under Telegram's 4096-char message limit."""
    chunks = []
    while len(text) > max_length:
        # Try to split at a newline near the limit
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    chunks.append(text)
    return chunks


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python send_telegram.py <markdown_file>", file=sys.stderr)
        sys.exit(1)

    md_path = sys.argv[1]
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Add a header
    header = "📰 *Daily AI Technology Briefing*\n\n"
    full_text = header + content

    chunks = split_message(full_text)
    for i, chunk in enumerate(chunks, 1):
        status, response = send_message(token, chat_id, chunk)
        if status != 200:
            print(f"Failed to send chunk {i}: {status} — {response}", file=sys.stderr)
            sys.exit(1)
        print(f"Chunk {i}/{len(chunks)} sent successfully.")

    print("Briefing delivered to Telegram.")


if __name__ == "__main__":
    main()
