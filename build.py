#!/usr/bin/env python3
"""
MHM Website Builder - Single Source of Truth
=============================================
Edit data.json with updated stats, then run:
    python3 build.py

This regenerates all stats in index.html from data.json.
"""

import json
import re
import os

DIR = os.path.dirname(os.path.abspath(__file__))

def load_data():
    with open(os.path.join(DIR, 'data.json'), 'r') as f:
        return json.load(f)

def load_html():
    with open(os.path.join(DIR, 'index.html'), 'r') as f:
        return f.read()

def save_html(content):
    with open(os.path.join(DIR, 'index.html'), 'w') as f:
        f.write(content)

def update_stats_bar(html, season_key, data):
    """Update the stats bar numbers."""
    d = data[season_key]
    old_pattern = f'<section class="stats-bar" data-league="{season_key}"[^>]*>'
    match = re.search(old_pattern, html)
    if not match:
        return html
    start = match.start()
    end = html.find('</section>', start) + len('</section>')
    style = ' style="display:none;"' if season_key != 'ccc-summer' else ''
    
    new_bar = f'''<section class="stats-bar" data-league="{season_key}"{style}>
        <div class="sbar"><span data-count="{d['matches']}">0</span>MATCHES</div>
        <div class="sbar"><span data-count="{d['wins']}">0</span>WINS</div>
        <div class="sbar"><span data-count="{d['totalRuns']}">0</span>RUNS</div>
        <div class="sbar"><span data-count="{d['losses']}">0</span>LOSSES</div>
        <div class="sbar accent"><span data-count="{d['winRate']}">0</span>WIN RATE</div>
    </section>'''
    
    html = html[:start] + new_bar + html[end:]
    print(f"  ✓ Stats bar updated for {season_key}")
    return html

def get_badge_html(badge):
    """Return styled badge HTML."""
    colors = {
        'CAPTAIN': ('var(--fire)', '#000'),
        'VICE CAPTAIN': ('var(--fire)', '#000'),
        '#1 RANKED': ('gold', '#000'),
        'TOP BOWLER': ('var(--red)', '#fff'),
        'TOP SCORER': ('var(--fire)', '#000'),
        'BEST BAT SR': ('var(--ember)', '#000'),
        'BEST ECONOMY': ('var(--green)', '#000'),
        'BEST BOWL AVG': ('var(--red)', '#fff'),
        'BEST BOWL SR': ('var(--red)', '#fff'),
        'TOP FIELDER': ('var(--green)', '#000'),
        'MOST RUN OUTS': ('var(--green)', '#000'),
        "MOST 6's": ('var(--ember)', '#000'),
        "MOST 4's": ('var(--green)', '#000'),
        'MOST DOT BALLS': ('#7c3aed', '#fff'),
        'MOM': ('gold', '#000'),
    }
    icons = {
        '#1 RANKED': '🥇', 'TOP BOWLER': '🔴', 'TOP SCORER': '🏏',
        'BEST BAT SR': '💥', 'BEST ECONOMY': '⚡', 'BEST BOWL AVG': '🎯',
        'BEST BOWL SR': '🎯', 'TOP FIELDER': '🤲', 'MOST RUN OUTS': '🏃',
        "MOST 6's": '', "MOST 4's": '', 'MOST DOT BALLS': '🎯', 'MOM': '⭐',
    }
    bg, fg = colors.get(badge, ('var(--fire)', '#000'))
    icon = icons.get(badge, '')
    prefix = f"{icon} " if icon else ""
    return f'<span class="sc-badge" style="background:{bg};color:{fg};">{prefix}{badge}</span>'

def update_squad_cards(html, season_key, data):
    """Update squad card stats and ranks."""
    d = data[season_key]
    players = d['players']
    
    for p in players:
        name = p['name']
        pos_marker = f'{name}</div><div class="sc-back-pos">MHM • {d["name"]}</div>'
        idx = html.find(pos_marker)
        if idx == -1:
            continue
        
        # Update rank text
        rank_start = html.find('<div class="sc-rank">', idx)
        if rank_start != -1 and rank_start < idx + 600:
            rank_end = html.find('</div>', rank_start)
            rank_num = players.index(p) + 1
            medal = ' 🥇' if rank_num == 1 else ''
            new_rank = f'<div class="sc-rank">Rank #{rank_num} • {p["total"]} pts{medal}</div>'
            html = html[:rank_start] + new_rank + html[rank_end + 6:]
    
    print(f"  ✓ Squad card ranks updated for {season_key}")
    return html

def update_rankings_table(html, season_key, data):
    """Regenerate the full rankings table."""
    d = data[season_key]
    players = sorted(d['players'], key=lambda x: x['total'], reverse=True)
    
    # Find the rankings table for this league
    marker = f'<div class="league-content" data-league="{season_key}"'
    idx = html.find(marker, html.find('PLAYER RANKINGS'))
    if idx == -1:
        print(f"  ✗ Rankings section not found for {season_key}")
        return html
    
    # Find rankings-table within this section
    table_start = html.find('<div class="rankings-table">', idx)
    if table_start == -1 or table_start > idx + 500:
        return html
    
    # Find end of table (before btn-show-all)
    header_end = html.find('</div>', html.find('rank-header', table_start)) + 6
    table_end = html.find('</div>\n', html.rfind('rank-row', table_start, html.find('btn-show-all', table_start)))
    table_end = html.find('\n', table_end) + 1
    
    # Build new rows
    rows = []
    medals = {0: '🥇', 1: '🥈', 2: '🥉'}
    classes = {0: ' gold', 1: ' silver', 2: ' bronze'}
    
    for i, p in enumerate(players):
        rank_display = medals.get(i, str(i+1))
        cls = classes.get(i, '')
        hidden = ' hidden-rank' if i >= 10 else ''
        negative = ' negative' if p['total'] <= 0 else ''
        row = f'            <div class="rank-row{cls}{hidden}{negative}" data-points="{p["total"]}"><span class="rank-col rank-num">{rank_display}</span><span class="rank-col rank-player">{p["name"]}</span><span class="rank-col">{p["mat"]}</span><span class="rank-col">{p["bat"]}</span><span class="rank-col">{p["bowl"]}</span><span class="rank-col">{p["field"]}</span><span class="rank-col">{p["mom"]}</span><span class="rank-col rank-total">{p["total"]}</span></div>'
        rows.append(row)
    
    new_rows = '\n'.join(rows) + '\n'
    
    # Replace between header end and table closing div
    first_row = html.find('<div class="rank-row', header_end)
    last_row_end = html.find('</div>\n        </div>', first_row)
    if first_row != -1 and last_row_end != -1:
        html = html[:first_row] + new_rows + '        ' + html[last_row_end:]
    
    print(f"  ✓ Rankings table updated for {season_key}")
    return html

def update_top_performers(html, season_key, data):
    """Update the top performers section."""
    d = data[season_key]
    players = d['players']
    
    # Find top scorer, top bowler, best econ, best SR
    top_scorer = max(players, key=lambda x: x['runs'])
    bowlers = [p for p in players if p['wkts'] > 0]
    top_bowler = min(bowlers, key=lambda x: x['econ'] if x['econ'] > 0 else 999) if bowlers else None
    top_wkts = max(bowlers, key=lambda x: x['wkts']) if bowlers else None
    batters_sr = [p for p in players if p['runs'] >= 15 and p['sr'] > 0]
    best_sr = max(batters_sr, key=lambda x: x['sr']) if batters_sr else None
    best_econ = min([p for p in players if p['econ'] > 0 and p['wkts'] >= 2], key=lambda x: x['econ']) if [p for p in players if p['econ'] > 0 and p['wkts'] >= 2] else None
    
    # Build performers HTML
    perf_html = '        <div class="performers">\n'
    perf_html += f'            <div class="perf"><div class="perf-icon">🏏</div><div class="perf-cat">TOP SCORER</div><div class="perf-name">{top_scorer["name"]}</div><div class="perf-val">{top_scorer["runs"]} runs</div></div>\n'
    if top_wkts:
        perf_html += f'            <div class="perf"><div class="perf-icon">🔴</div><div class="perf-cat">TOP WICKETS</div><div class="perf-name">{top_wkts["name"]}</div><div class="perf-val">{top_wkts["wkts"]} wkts</div></div>\n'
    if best_econ:
        perf_html += f'            <div class="perf"><div class="perf-icon">⚡</div><div class="perf-cat">BEST ECONOMY</div><div class="perf-name">{best_econ["name"]}</div><div class="perf-val">{best_econ["econ"]}</div></div>\n'
    if best_sr:
        perf_html += f'            <div class="perf"><div class="perf-icon">💥</div><div class="perf-cat">BEST SR (BAT)</div><div class="perf-name">{best_sr["name"]}</div><div class="perf-val">{best_sr["sr"]}</div></div>\n'
    perf_html += '        </div>'
    
    # Find and replace performers div
    marker = f'data-league="{season_key}"'
    stats_section = html.find('TOP PERFORMERS')
    league_start = html.find(marker, stats_section)
    if league_start == -1:
        return html
    
    perf_start = html.find('<div class="performers">', league_start)
    perf_end = html.find('</div>\n\n', perf_start) + 6
    if perf_start != -1 and perf_start < league_start + 200:
        html = html[:perf_start] + perf_html + html[perf_end:]
    
    print(f"  ✓ Top performers updated for {season_key}")
    return html


def main():
    print("🏏 MHM Website Builder")
    print("=" * 40)
    print()
    
    data = load_data()
    html = load_html()
    
    for season_key in data:
        print(f"Processing: {data[season_key]['name']}")
        html = update_stats_bar(html, season_key, data)
        html = update_squad_cards(html, season_key, data)
        # Rankings and performers only for completed seasons
        if data[season_key].get('status') == 'completed':
            html = update_rankings_table(html, season_key, data)
            html = update_top_performers(html, season_key, data)
        print()
    
    save_html(html)
    print("✅ Done! index.html updated from data.json")
    print("   Review changes and push when ready.")


if __name__ == "__main__":
    main()
