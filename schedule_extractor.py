"""
Schedule Extractor for Lars
===========================

Lars's roster is a single-person, per-period report ("Concept Medewerker
Rooster") produced by BVCM. Unlike Sam's monthly grid, this is a *vertical*
list of days. Every row carries its own full date (DD/MM/YYYY) and zero or more
shift entries.

Format (one block per day):

    Vrijdag 01/05/2026 DIENST 00:00-07:00 00:00-02:15 Surveilleren ...
                       DIENST 22:00-24:00 22:00-24:00 Surveilleren ...
    Zaterdag 02/05/2026 [Rust] 00:00-24:00

So there is no table geometry to recover (no cell_detector needed). We parse the
text line-by-line:

  - A line starting with a weekday + date opens a new day.
  - Each `DIENST HH:MM-HH:MM ...` is one worked shift; the FIRST time range
    after "DIENST" is the shift envelope (start-end). The remaining ranges on
    the line are the internal time breakdown (Tijdstippen / Pauze) and are
    ignored.
  - `[Rust]` / `[Vr.zondag]` lines are time off and produce no shift.

Shift envelopes are collected into a set keyed by (date, start, end). This
naturally de-duplicates the day/shift headers that BVCM repeats across page
breaks (a shift split over two pages prints its header on both).

Privacy note: we deliberately keep only date + start/end times. Memos, activity
descriptions, project codes, locations and event names are NOT extracted, so
they can never leak into the published HTML.
"""

import re
import calendar
import pdfplumber
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

WEEKDAYS_NL = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]

# A row that opens a new day, e.g. "Vrijdag 01/05/2026 ..."
DATE_RE = re.compile(r"^(" + "|".join(WEEKDAYS_NL) + r")\s+(\d{2})/(\d{2})/(\d{4})")

# A time range, e.g. "00:00-07:00"
TIME_RE = re.compile(r"(\d{2}:\d{2})-(\d{2}:\d{2})")


class ScheduleExtractor:
    """Extract Lars's worked shifts from a BVCM period roster PDF."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_schedule(self) -> pd.DataFrame:
        """
        Parse the PDF and return a DataFrame with one row per shift envelope.

        Columns: Date (YYYY-MM-DD), Day (weekday name, English), Start, End.
        """
        # Use a set so shift headers repeated across page breaks collapse.
        shifts: set[tuple[str, str, str]] = set()
        current_date: str | None = None

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for raw_line in text.split("\n"):
                    line = raw_line.strip()
                    if not line:
                        continue

                    # Does this line open a new day?
                    m = DATE_RE.match(line)
                    rest = line
                    if m:
                        _, dd, mm, yyyy = m.groups()
                        current_date = f"{yyyy}-{mm}-{dd}"
                        rest = line[m.end():].strip()

                    # Is this (the remainder of) a worked shift?
                    if rest.startswith("DIENST") and current_date:
                        tm = TIME_RE.search(rest)
                        if tm:
                            shifts.add((current_date, tm.group(1), tm.group(2)))

        records = []
        for date, start, end in sorted(shifts):
            year, month, day = (int(x) for x in date.split("-"))
            weekday = calendar.day_name[calendar.weekday(year, month, day)]
            records.append({
                "Date": date,
                "Day": weekday,
                "Start": start,
                "End": end,
            })

        return pd.DataFrame(records, columns=["Date", "Day", "Start", "End"])


def main():
    """Quick standalone test against the sample PDFs."""
    for pdf_path in ["./pdfs/Rooster periode 5.pdf", "./pdfs/Rooster periode 6.pdf"]:
        print("=" * 60)
        print(pdf_path)
        df = ScheduleExtractor(pdf_path).extract_schedule()
        print(f"{len(df)} shift envelopes across {df['Date'].nunique()} days")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
