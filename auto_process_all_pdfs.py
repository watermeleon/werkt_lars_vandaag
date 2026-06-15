"""
Batch-process all of Agent L's roster PDFs into a single combined CSV.

Each PDF is a BVCM period roster that already contains full ISO dates per row,
so (unlike Sam's pipeline) there is no need to parse month/year/location from
the filename. We simply extract every PDF in ./pdfs/, concatenate, de-duplicate
on (Date, Start, End) in case period PDFs overlap, and write one CSV.
"""

from pathlib import Path
import time
import pandas as pd

from schedule_extractor import ScheduleExtractor


def process_all_pdfs(source_path: str, dest_file: str) -> pd.DataFrame:
    """Extract every PDF in `source_path` and write a combined CSV to `dest_file`."""
    pdf_files = sorted(Path(source_path).glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {source_path}\n")

    all_frames = []
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        start = time.time()
        try:
            df = ScheduleExtractor(str(pdf_path)).extract_schedule()
            print(f"  Extracted {len(df)} shifts in {time.time() - start:.2f}s")
            all_frames.append(df)
        except Exception as e:
            print(f"  FAILED: {e}")

    if not all_frames:
        print("No data extracted.")
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    # Overlapping periods can list the same shift twice; keep one.
    combined = (
        combined.drop_duplicates(subset=["Date", "Start", "End"])
        .sort_values(["Date", "Start"])
        .reset_index(drop=True)
    )

    Path(dest_file).parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(dest_file, index=False)

    print(f"\nSaved {len(combined)} shifts across {combined['Date'].nunique()} days")
    print(f"  -> {dest_file}")
    return combined


def main():
    process_all_pdfs(
        source_path="./pdfs/",
        dest_file="./extracted_schedules/L_schedule.csv",
    )


if __name__ == "__main__":
    main()
