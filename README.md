# pmt-scraper

Download and organise PDFs from [Physics & Maths Tutor](https://www.physicsandmathstutor.com/) pages.

Point it at any PMT page that lists PDF links and it scrapes every PDF, sorts them into folders, and downloads them politely (rate-limited, resumable, skips existing files).

## Install

```bash
pip install requests beautifulsoup4
```

## Usage

```bash
python pmt_scrape.py <url> [options]
```

## Options

### Output

| Flag | Default | Description |
|------|---------|-------------|
| `--out <dir>` | `downloads` | Root output folder |
| `--organise heading` | ✓ | Group by section heading on the page |
| `--organise path` | | Mirror PMT's own folder structure |
| `--organise flat` | | All files in one folder |
| `--delay <secs>` | `1.0` | Pause between downloads (be polite) |
| `--dry-run` | | Print what would be saved, download nothing |

### Filtering

| Flag | Description |
|------|-------------|
| `--keywords k1 k2 …` | Filter by keywords — see syntax below |
| `--years y1 y2 …` | Keep only PDFs mentioning **any** of these years |
| `--year-range FROM TO` | Keep only PDFs whose year falls within FROM–TO (inclusive) |

`--years` and `--year-range` can be used together; both constraints must pass (AND).

**Keyword syntax** — prefix each token to control how it matches:

| Prefix | Meaning |
|--------|---------|
| `word` or `+word` | Must be present (positive) |
| `-word` | Must be absent (negative) |

Matching is case-insensitive and searches the section heading, link text, and filename.
Years embedded in PMT's URL paths (e.g. `.../2019/...`) are detected automatically.
Undated files are always kept.

## Examples

```bash
# All papers, grouped by heading
python pmt_scrape.py https://www.physicsandmathstutor.com/maths-revision/a-level-papers/

# Mark schemes only
python pmt_scrape.py <url> --keywords "mark scheme"

# Mark schemes only (positive keyword)
python pmt_scrape.py <url> --keywords +markscheme

# Mark schemes, excluding question papers
python pmt_scrape.py <url> --keywords +markscheme -questions

# Papers from 2018 to 2022
python pmt_scrape.py <url> --year-range 2018 2022

# Mark schemes for specific years (combine --years and --year-range)
python pmt_scrape.py <url> --keywords +markscheme --years 2019 2021 2023 --year-range 2019 2023

# Paper 1 only, no mark schemes, preview before downloading
python pmt_scrape.py <url> --keywords +paper1 -markscheme --dry-run

# Mirror PMT's folder structure
python pmt_scrape.py <url> --organise path
```

## Project structure

```
pmt scraper/
├── pmt_scrape.py          # entry point
├── pmt_scraper/
│   ├── __init__.py
│   ├── cli.py             # argument parsing and main loop
│   ├── scraper.py         # page fetching and PDF link extraction
│   ├── downloader.py      # file download and output path logic
│   ├── filters.py         # keyword and year filtering
│   └── utils.py           # filename sanitisation, URL helpers
└── downloads/             # default output folder
```

## Notes

- Downloads use a `.part` suffix until complete — interrupted runs are safe to resume.
- Files already present (non-zero size) are skipped automatically.
- Pages that load links via JavaScript will not work; PMT's static pages are fine.
