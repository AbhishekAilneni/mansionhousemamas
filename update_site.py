#!/usr/bin/env python3
"""
Auto-update Mansion House Mamas website from CricClubs.

Uses Selenium (headless Chrome) to bypass Cloudflare and fetch real data.

Usage:
    python3 update_site.py

First time setup:
    pip install selenium
    (Chrome browser must be installed)
"""

import os
import re
import time
import json

TEAM_URL = "https://cricclubs.com/CarolinaCricketChampionship/viewTeam.do?teamId=283&league=23&clubId=1093111"
SITE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=opts)
    return driver


def fetch_team_data():
    print("  Starting Chrome...")
    driver = get_driver()

    try:
        print(f"  Loading team page...")
        driver.get(TEAM_URL)
        # Wait for Cloudflare challenge to pass
        time.sleep(8)

        html = driver.page_source
        print(f"  Got {len(html)} bytes")

        # Extract players
        players = re.findall(r'viewPlayer[^"]*"[^>]*>([^<]+)</a>', html)
        players = [p.strip() for p in players if len(p.strip()) > 2]
        # Deduplicate
        seen = set()
        unique_players = []
        for p in players:
            if p not in seen:
                seen.add(p)
                unique_players.append(p)

        print(f"  Players: {unique_players[:10]}")

        # Extract match results (scores like 142/5)
        scores = re.findall(r'(\d+/\d+)', html)
        print(f"  Scores found: {scores[:10]}")

        # Try to get schedule page
        schedule_url = TEAM_URL.replace('viewTeam', 'viewSchedule')
        print(f"  Loading schedule...")
        driver.get(schedule_url)
        time.sleep(6)
        sched_html = driver.page_source

        # Extract upcoming matches and results from schedule
        # CricClubs uses table rows with team names
        teams_in_schedule = re.findall(r'viewTeam[^"]*"[^>]*>([^<]+)</a>', sched_html)
        sched_scores = re.findall(r'(\d+/\d+)', sched_html)
        dates = re.findall(r'(\w{3}\s+\d{1,2},\s*\d{4})', sched_html)

        print(f"  Schedule teams: {teams_in_schedule[:10]}")
        print(f"  Schedule scores: {sched_scores[:10]}")
        print(f"  Dates: {dates[:10]}")

        # Save raw data for manual inspection
        data = {
            'players': unique_players,
            'scores': scores[:20],
            'schedule_teams': teams_in_schedule[:20],
            'schedule_scores': sched_scores[:20],
            'dates': dates[:10],
        }

        data_path = os.path.join(SITE_DIR, 'team_data.json')
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved raw data to team_data.json")

        return data

    finally:
        driver.quit()


def update_html(data):
    """Update index.html with fetched data."""
    html_path = os.path.join(SITE_DIR, 'index.html')
    with open(html_path, 'r') as f:
        html = f.read()

    players = data.get('players', [])

    # Replace player names
    if players:
        replacements = [
            ('Your Captain', players[0]),
            ('Captain Name', players[0]),
            ('Player Two', players[1] if len(players) > 1 else 'Player 2'),
            ('Player Three', players[2] if len(players) > 2 else 'Player 3'),
            ('Player Four', players[3] if len(players) > 3 else 'Player 4'),
            ('Player Five', players[4] if len(players) > 4 else 'Player 5'),
            ('Player Six', players[5] if len(players) > 5 else 'Player 6'),
        ]
        for old, new in replacements:
            html = html.replace(old, new)

    with open(html_path, 'w') as f:
        f.write(html)
    print(f"  ✅ HTML updated with {len(players)} player names")


def main():
    print("🏏 Updating Mansion House Mamas website from CricClubs...")
    print()

    data = fetch_team_data()
    print()

    if data and data.get('players'):
        update_html(data)
    else:
        print("  ⚠️  No data fetched. Check team_data.json for raw output.")

    print()
    print("  Done! Open index.html to see updates.")
    print("  Raw data saved in team_data.json for reference.")


if __name__ == "__main__":
    main()
