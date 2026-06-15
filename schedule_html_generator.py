"""
Generate the interactive HTML viewer for Agent L's schedule.

Reads the combined CSV produced by auto_process_all_pdfs.py and emits a
self-contained HTML page (docs/index.html) with an embedded JSON blob of
{date -> [shift time ranges]}. Only dates and start/end times are embedded;
no memos, activities or locations from the source PDFs.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List


def generate_schedule_html(
    csv_path: str,
    output_file: str = "./docs/index.html",
    start_date: str = None,
) -> str:
    print("Reading schedule file...")
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"No schedule data in {csv_path}")
    print(f"Loaded {len(df)} shifts across {df['Date'].nunique()} days")

    schedule_by_date = prepare_schedule_data(df)
    html_content = generate_html_content(schedule_by_date, start_date)

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✓ HTML schedule generated: {output_file}")
    return output_file


def prepare_schedule_data(df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """Return {date: [{'start':..,'end':..}, ...]} sorted by start time."""
    by_date: Dict[str, List[Dict]] = {}
    for _, row in df.iterrows():
        date = str(row["Date"]).strip()
        start = str(row["Start"]).strip()
        end = str(row["End"]).strip()
        if not date or date == "nan":
            continue
        by_date.setdefault(date, []).append({"start": start, "end": end})
    for shifts in by_date.values():
        shifts.sort(key=lambda s: s["start"])
    return by_date


def generate_html_content(schedule_by_date: Dict[str, List[Dict]], start_date: str = None) -> str:
    schedule_json = json.dumps(schedule_by_date, indent=2)

    if start_date:
        initial_date = start_date
    else:
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        initial_date = monday.strftime("%Y-%m-%d")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Werkt Agent L Vandaag?</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        /* ===== Base: Medical Dashboard (dark, default) ===== */
        body {{
            background: #1b2332;
            font-family: 'Segoe UI', system-ui, sans-serif;
            padding: 20px;
            color: #dce4ee;
            transition: background 0.3s, color 0.3s;
        }}
        .container {{
            max-width: 760px;
            margin: 0 auto;
            background: #232d3f;
            border: 1px solid #3a4556;
            border-radius: 8px;
            box-shadow: 0 0 30px rgba(0,0,0,0.4);
            overflow: hidden;
            transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
        }}
        .header {{
            background: linear-gradient(135deg, #1a4a7a 0%, #2a2a4e 100%);
            border-bottom: 2px solid #00ff41;
            color: white;
            padding: 18px;
            text-align: center;
            position: relative;
            transition: background 0.3s, border-color 0.3s;
        }}
        .header h1 {{
            font-family: 'Courier New', monospace;
            font-size: 28px;
            margin-bottom: 5px;
            letter-spacing: 2px;
        }}
        .header p {{
            color: #00ff41;
            font-family: 'Courier New', monospace;
            font-size: 15px;
            letter-spacing: 1px;
            transition: color 0.3s;
        }}
        .week-navigator {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            background: #1e2838;
            border-bottom: 1px solid #3a4556;
            flex-wrap: wrap;
            gap: 10px;
            transition: background 0.3s, border-color 0.3s;
        }}
        .week-info {{
            font-size: 18px;
            font-weight: 600;
            color: #dce4ee;
            font-family: 'Courier New', monospace;
            flex: 1;
            text-align: center;
            min-width: 250px;
            transition: color 0.3s;
        }}
        .nav-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .btn {{
            padding: 10px 20px;
            border: 1px solid #3a4556;
            border-radius: 4px;
            background: #2a3548;
            color: #dce4ee;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }}
        .btn:hover {{
            background: #354460;
            border-color: #00ff41;
            color: #00ff41;
        }}
        .btn:active {{
            transform: scale(0.98);
        }}
        .btn-success {{
            background: rgba(0,255,65,0.12);
            border-color: #00ff41;
            color: #00ff41;
        }}
        .btn-success:hover {{
            background: rgba(0,255,65,0.22);
        }}
        .days-container {{
            padding: 15px;
        }}
        .day-card {{
            background: linear-gradient(135deg, #263040 0%, #2a3750 100%);
            border-radius: 4px;
            padding: 10px 14px;
            margin-bottom: 8px;
            border-left: 4px solid #3d8ecf;
            transition: all 0.2s;
        }}
        .day-card:hover {{
            border-left-color: #5bb8ff;
            background: linear-gradient(135deg, #2a364a 0%, #2f3e58 100%);
        }}
        .day-card.no-shift {{
            opacity: 0.55;
            border-left-color: #3a4556;
            background: #232d3f;
        }}
        .day-card.current-day {{
            border-left: 5px solid #00ff41;
            background: linear-gradient(135deg, #1a3a2a 0%, #1e4032 100%);
            box-shadow: 0 0 18px rgba(0,255,65,0.15), inset 0 0 30px rgba(0,255,65,0.04);
        }}
        .day-card.current-day:hover {{
            background: linear-gradient(135deg, #1e4030 0%, #224838 100%);
        }}
        .day-card.current-day .day-name {{
            color: #44ff77;
        }}
        .day-card.current-day .shift-time {{
            color: #a0f0b8;
        }}
        .day-card.current-day .no-shift-message {{
            color: #70c090;
        }}
        .day-card.current-day .day-date {{
            color: #80d0a0;
        }}
        .current-day-badge {{
            display: inline-block;
            background: #00ff41;
            color: #0d1117;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
            font-family: 'Courier New', monospace;
            letter-spacing: 1px;
            transition: background 0.3s, color 0.3s;
        }}
        .day-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }}
        .day-name {{
            font-weight: 700;
            font-size: 16px;
            color: #e4eaf2;
            transition: color 0.3s;
        }}
        .day-date {{
            font-size: 13px;
            color: #cdd5e0;
            font-family: 'Courier New', monospace;
            transition: color 0.3s;
        }}
        .shift-info {{
            margin-top: 2px;
        }}
        .shift-time {{
            font-size: 15px;
            font-weight: 600;
            color: #d0d8e4;
            font-family: 'Courier New', monospace;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
            transition: color 0.3s;
        }}
        .no-shift-message {{
            color: #7888a0;
            font-style: italic;
            font-family: 'Courier New', monospace;
            transition: color 0.3s;
        }}
        .easter-egg {{
            text-align: center;
            padding: 15px;
            font-size: 12px;
            color: #3a6a4a;
            cursor: pointer;
            user-select: none;
            transition: color 0.3s;
        }}
        .easter-egg:hover {{
            color: #50e070;
        }}

        /* ===== Theme Toggle Button ===== */
        .theme-toggle {{
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 50%;
            width: 38px;
            height: 38px;
            cursor: pointer;
            font-size: 20px;
            line-height: 38px;
            text-align: center;
            transition: all 0.3s;
            padding: 0;
            color: white;
        }}
        .theme-toggle:hover {{
            background: rgba(255,255,255,0.25);
            transform: translateY(-50%) scale(1.1);
        }}

        /* ===== Light Mode Overrides ===== */
        body.theme-light {{
            background: #f5f5f5;
            color: #333;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }}
        .theme-light .container {{
            background: white;
            border: none;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .theme-light .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-bottom: none;
        }}
        .theme-light .header h1 {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            letter-spacing: normal;
        }}
        .theme-light .header p {{
            color: rgba(255,255,255,0.9);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: inherit;
            letter-spacing: normal;
        }}
        .theme-light .week-navigator {{
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        .theme-light .week-info {{
            color: #495057;
            font-family: inherit;
        }}
        .theme-light .btn {{
            background: #667eea;
            border: none;
            border-radius: 6px;
            color: white;
        }}
        .theme-light .btn:hover {{
            background: #5568d3;
            color: white;
        }}
        .theme-light .btn-success {{
            background: #28a745;
            color: white;
        }}
        .theme-light .btn-success:hover {{
            background: #218838;
            color: white;
        }}
        .theme-light .day-card {{
            background: white;
            border-left: 4px solid #667eea;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }}
        .theme-light .day-card:hover {{
            background: white;
            border-left-color: #667eea;
        }}
        .theme-light .day-card.no-shift {{
            opacity: 0.5;
            border-left-color: #dee2e6;
            background: white;
        }}
        .theme-light .day-card.current-day {{
            border-left: 6px solid #28a745;
            background: #f0fff4;
            box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
        }}
        .theme-light .day-card.current-day:hover {{
            background: #f0fff4;
        }}
        .theme-light .day-card.current-day .day-name {{
            color: #28a745;
        }}
        .theme-light .day-card.current-day .shift-time {{
            color: #212529;
        }}
        .theme-light .day-card.current-day .no-shift-message {{
            color: #6c757d;
        }}
        .theme-light .day-card.current-day .day-date {{
            color: #6c757d;
        }}
        .theme-light .current-day-badge {{
            background: #28a745;
            color: white;
            font-family: inherit;
            letter-spacing: normal;
        }}
        .theme-light .day-name {{
            color: #495057;
        }}
        .theme-light .day-date {{
            color: #6c757d;
            font-family: inherit;
        }}
        .theme-light .shift-time {{
            color: #212529;
        }}
        .theme-light .no-shift-message {{
            color: #6c757d;
            font-family: inherit;
        }}
        .theme-light .easter-egg {{
            color: #ccc;
        }}
        .theme-light .easter-egg:hover {{
            color: #999;
        }}

        /* ===== Animations & Misc ===== */
        .glitter-particle {{
            position: fixed;
            pointer-events: none;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: glitter-fall linear forwards;
            z-index: 9999;
        }}
        @keyframes glitter-fall {{
            0% {{
                opacity: 1;
                transform: translateY(0) rotate(0deg) scale(1);
            }}
            100% {{
                opacity: 0;
                transform: translateY(100vh) rotate(720deg) scale(0.5);
            }}
        }}
        @keyframes float-up {{
            to {{
                transform: translateY(-120vh);
                opacity: 0;
            }}
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 22px;
                letter-spacing: 0.5px;
                padding-right: 40px;
            }}
            .week-navigator {{
                flex-direction: column;
                gap: 15px;
            }}
            .nav-buttons {{
                width: 100%;
                justify-content: center;
            }}
            .week-info {{
                order: -1;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>\U0001F4C5 Werkt Agent L Vandaag?</h1>
            <p>Weekly Overview</p>
            <button class="theme-toggle" onclick="toggleTheme()" id="themeToggle" title="Toggle light/dark mode">☀️</button>
        </div>

        <div class="week-navigator">
            <div class="week-info" id="weekInfo">Loading...</div>
            <div class="nav-buttons">
                <button class="btn" onclick="previousWeek()">← Previous</button>
                <button class="btn btn-success" onclick="goToCurrentWeek()">Current Week</button>
                <button class="btn" onclick="nextWeek()">Next →</button>
            </div>
        </div>

        <div class="days-container" id="scheduleContainer">
            <!-- Schedule will be populated by JavaScript -->
        </div>
        <div class="easter-egg" onclick="triggerGlitterBomb()">secret to happiness</div>
    </div>

    <script>
        // Embedded schedule data: {{ "YYYY-MM-DD": [{{start, end}}, ...] }}
        const scheduleByDate = {schedule_json};

        let currentWeekStart = getMonday(new Date());

        function getMonday(date) {{
            const d = new Date(date);
            const day = d.getDay();
            const diff = d.getDate() - day + (day === 0 ? -6 : 1);
            return new Date(d.setDate(diff));
        }}

        function formatDate(date) {{
            const options = {{ year: 'numeric', month: 'long', day: 'numeric' }};
            return date.toLocaleDateString('en-US', options);
        }}

        function formatDateShort(date) {{
            const options = {{ month: 'short', day: 'numeric' }};
            return date.toLocaleDateString('en-US', options);
        }}

        function getDateString(date) {{
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${{year}}-${{month}}-${{day}}`;
        }}

        function isToday(date) {{
            const today = new Date();
            return date.getDate() === today.getDate() &&
                   date.getMonth() === today.getMonth() &&
                   date.getFullYear() === today.getFullYear();
        }}

        function goToCurrentWeek() {{
            currentWeekStart = getMonday(new Date());
            renderSchedule();
        }}

        function renderSchedule() {{
            const monday = getMonday(currentWeekStart);
            const sunday = new Date(monday);
            sunday.setDate(sunday.getDate() + 6);

            document.getElementById('weekInfo').textContent =
                `${{formatDate(monday)}} - ${{formatDate(sunday)}}`;

            const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
            let html = '';

            for (let i = 0; i < 7; i++) {{
                const date = new Date(monday);
                date.setDate(date.getDate() + i);
                const dateStr = getDateString(date);
                const dayName = daysOfWeek[i];
                const today = isToday(date);

                const shifts = scheduleByDate[dateStr];

                if (shifts && shifts.length) {{
                    const times = shifts
                        .map(s => `⏱️ ${{s.start}} – ${{s.end}}`)
                        .join('<br>');
                    html += `
                        <div class="day-card${{today ? ' current-day' : ''}}">
                            <div class="day-header">
                                <div class="day-name">
                                    ${{dayName}}
                                    ${{today ? '<span class="current-day-badge">TODAY</span>' : ''}}
                                </div>
                                <div class="day-date">${{formatDateShort(date)}}</div>
                            </div>
                            <div class="shift-info">
                                <div class="shift-time">${{times}}</div>
                            </div>
                        </div>
                    `;
                }} else {{
                    html += `
                        <div class="day-card no-shift${{today ? ' current-day' : ''}}">
                            <div class="day-header">
                                <div class="day-name">
                                    ${{dayName}}
                                    ${{today ? '<span class="current-day-badge">TODAY</span>' : ''}}
                                </div>
                                <div class="day-date">${{formatDateShort(date)}}</div>
                            </div>
                            <div class="no-shift-message">No shift scheduled</div>
                        </div>
                    `;
                }}
            }}

            document.getElementById('scheduleContainer').innerHTML = html;
        }}

        function previousWeek() {{
            currentWeekStart.setDate(currentWeekStart.getDate() - 7);
            renderSchedule();
        }}

        function nextWeek() {{
            currentWeekStart.setDate(currentWeekStart.getDate() + 7);
            renderSchedule();
        }}

        function triggerGlitterBomb() {{
            const colors = [
                '#FFD700', '#FF1493', '#00CED1', '#FF69B4', '#9370DB',
                '#FF6347', '#00FA9A', '#FFA500', '#FF00FF', '#00FFFF'
            ];
            const particleCount = 1000;
            for (let i = 0; i < particleCount; i++) {{
                setTimeout(() => {{
                    const particle = document.createElement('div');
                    particle.className = 'glitter-particle';
                    particle.style.left = Math.random() * 100 + 'vw';
                    particle.style.top = '-10px';
                    particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                    particle.style.width = (Math.random() * 15 + 4) + 'px';
                    particle.style.height = particle.style.width;
                    particle.style.animationDuration = (Math.random() * 3 + 2) + 's';
                    particle.style.boxShadow = `0 0 ${{Math.random() * 10 + 5}}px ${{colors[Math.floor(Math.random() * colors.length)]}}`;
                    document.body.appendChild(particle);
                    setTimeout(() => particle.remove(), 6000);
                }}, Math.random() * 500);
            }}
            for (let i = 0; i < 150; i++) {{
                setTimeout(() => {{
                    const balloon = document.createElement('div');
                    const drift = Math.random() * 60 - 30;
                    balloon.style.position = 'fixed';
                    balloon.style.left = Math.random() * 90 + 5 + 'vw';
                    balloon.style.bottom = '-80px';
                    balloon.style.width = (Math.random() * 40 + 50) + 'px';
                    balloon.style.height = (Math.random() * 50 + 60) + 'px';
                    balloon.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                    balloon.style.borderRadius = '50% 50% 45% 45%';
                    balloon.style.opacity = '0.85';
                    balloon.style.boxShadow = `inset -10px -10px 20px rgba(0,0,0,0.2), 0 0 20px ${{colors[Math.floor(Math.random() * colors.length)]}}`;
                    balloon.style.animation = `float-up ${{Math.random() * 3 + 4}}s ease-out forwards`;
                    balloon.style.transform = `translateX(${{drift}}px)`;
                    balloon.style.zIndex = '9999';
                    document.body.appendChild(balloon);
                    setTimeout(() => balloon.remove(), 8000);
                }}, Math.random() * 1000);
            }}
        }}

        let isDarkMode = true;
        function toggleTheme() {{
            isDarkMode = !isDarkMode;
            document.body.classList.toggle('theme-light', !isDarkMode);
            document.getElementById('themeToggle').textContent = isDarkMode ? '☀️' : '\U0001F319';
        }}

        renderSchedule();
    </script>
</body>
</html>"""

    return html


if __name__ == "__main__":
    generate_schedule_html(
        csv_path="./extracted_schedules/L_schedule.csv",
        output_file="./docs/index.html",
    )
