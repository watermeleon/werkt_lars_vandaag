# Werkt Lars Vandaag?

A small site that shows Lars's work schedule, generated from the period
roster PDFs Lars receives. Same idea as the companion `werkt_sam_vandaag` repo, but
Lars's roster has a completely different layout, so the extraction step is new.

## Steps

```bash
# 1. Extract every PDF in ./pdfs/ into one combined CSV
python auto_process_all_pdfs.py

# 2. Turn the CSV into the viewable HTML page (docs/index.html)
python schedule_html_generator.py
```

## How Lars's roster differs from Sam's

| | Sam | Lars |
|---|---|---|
| PDF layout | Monthly **grid**: employees × days, shift codes (N/D/A) | Per-period **list**: one block per day with full dates |
| Shift value | Single letter code | Actual time ranges (`00:00-07:00`) |
| People per PDF | Many (filter to Sam) | Just Lars |
| Extraction | `cell_detector.py` recovers table geometry | Plain line/text parse — no geometry needed |

Because Lars's PDF is a generated BVCM report ("Concept Medewerker Rooster") where
every row carries its own date, extraction is just text parsing.

## Understanding the code

- `schedule_extractor.py` — opens each PDF, walks the text line by line. A line
  starting with a weekday + date opens a new day; each `DIENST HH:MM-HH:MM` is a
  worked shift whose first time range is the start–end envelope. `[Rust]` /
  `[Vr.zondag]` lines are time off and are skipped. Shifts go into a set keyed by
  `(date, start, end)`, which de-duplicates the headers BVCM repeats across page
  breaks.
- `auto_process_all_pdfs.py` — runs the extractor over every PDF in `./pdfs/`,
  concatenates, de-duplicates overlapping periods, and writes
  `extracted_schedules/lars_schedule.csv`.
- `schedule_html_generator.py` — builds `docs/index.html`, a single-week viewer
  with previous/next navigation, current-day highlight, and light/dark themes.

## Privacy

- The source PDFs (`pdfs/`) and the extracted CSV (`extracted_schedules/`) are
  git-ignored — they are never committed.
- Only the **date and shift start/end times** are embedded in the published
  `docs/index.html`. Memos, activity descriptions, project codes, locations and
  event names from the PDFs are deliberately **not** extracted, so they cannot
  leak into the public page.
