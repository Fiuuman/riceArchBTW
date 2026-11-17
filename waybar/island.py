#!/usr/bin/env python3
import subprocess
import json
import os
import urllib.request
import urllib.parse
import time
import html

COVER_PATH = "/tmp/waybar_cover.jpg"
last_art_url = ""

def get_active_window():
    try:
        out = subprocess.check_output(["hyprctl", "activewindow", "-j"], stderr=subprocess.DEVNULL).decode()
        title = json.loads(out).get("title", "")
        if len(title) > 55:
            title = title[:52] + "..."
        return html.escape(title)
    except Exception:
        return ""

def get_meta(player, key):
    try:
        return subprocess.check_output(
            ["playerctl", "-p", player, "metadata", key],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return ""

def get_player_info():
    try:
        players = subprocess.check_output(["playerctl", "-l"], stderr=subprocess.DEVNULL).decode().splitlines()
    except Exception:
        return None

    for p in players:
        try:
            status = subprocess.check_output(["playerctl", "-p", p, "status"], stderr=subprocess.DEVNULL).decode().strip()
            if status != "Playing":
                continue

            title = get_meta(p, "title")
            artist = get_meta(p, "artist")
            art_url = get_meta(p, "mpris:artUrl")

            # Если в файле из Telegram не прописаны теги, берём имя файла из URL
            if not title:
                url = get_meta(p, "xesam:url")
                if url:
                    filename = os.path.basename(urllib.parse.unquote(url))
                    title = os.path.splitext(filename)[0]

            if title:
                return title, artist, art_url
        except Exception:
            continue
    return None

def update_cover(art_url):
    global last_art_url
    if not art_url:
        return False
    if art_url == last_art_url and os.path.exists(COVER_PATH):
        return True
    try:
        if art_url.startswith("file://"):
            os.system(f"cp '{art_url[7:]}' {COVER_PATH}")
            last_art_url = art_url
            return True
        elif art_url.startswith("http"):
            urllib.request.urlretrieve(art_url, COVER_PATH)
            last_art_url = art_url
            return True
    except Exception:
        pass
    return False

while True:
    info = get_player_info()
    if not info:
        win_title = get_active_window()
        if not win_title:
            print(json.dumps({"text": "", "class": "empty"}), flush=True)
        else:
            print(json.dumps({"text": f"  {win_title}  ", "class": "window"}), flush=True)
        time.sleep(0.25)
        continue

    title, artist, art_url = info
    has_cover = update_cover(art_url)

    track_text = f"{artist} — {title}" if artist else title
    if len(track_text) > 40:
        track_text = track_text[:37] + "..."
    track_text = html.escape(track_text)

    if has_cover:
        output = {
            "text": f" {track_text} ",
            "tooltip": f"{artist} — {title}",
            "class": "playing"
        }
    else:
        # Если у трека из ТГ нет обложки — рисуем аккуратную ноту
        output = {
            "text": f"     {track_text} ",
            "tooltip": f"{artist} — {title}",
            "class": "playing-nocover"
        }

    print(json.dumps(output), flush=True)
    time.sleep(0.25)
