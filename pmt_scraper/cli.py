import argparse
import sys

from .scraper import scrape_links
from .downloader import download, target_path
from .filters import apply_filters, parse_keywords
from .utils import page_slug


def _build_parser():
    ap = argparse.ArgumentParser(
        description="Scrape and organise PDFs from a PMT page.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
keyword syntax:
  bare word or +word  →  must be present  (positive)
  -word               →  must be absent   (negative)

examples:
  %(prog)s <url>
  %(prog)s <url> --keywords +markscheme -questions
  %(prog)s <url> --keywords markscheme --years 2019 2020 2021
  %(prog)s <url> --year-range 2018 2022
  %(prog)s <url> --keywords +paper1 -markscheme --year-range 2019 2023 --years 2019 2021 2023
  %(prog)s <url> --dry-run
""",
    )

    ap.add_argument("url", help="PMT page URL to scrape")
    ap.add_argument("-o", "--output", "--out", dest="output", default="downloads",
                    metavar="DIR",
                    help="Folder to save PDFs into (default: downloads)")
    ap.add_argument("--organise", choices=["heading", "path", "flat"], default="heading",
                    help="How to group files: heading (default), path, or flat")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="Seconds to wait between downloads (default: 1.0)")
    ap.add_argument("--dry-run", action="store_true",
                    help="List what would be downloaded without downloading")

    filt = ap.add_argument_group("filtering")
    filt.add_argument(
        "--keywords", nargs="+", metavar="KEYWORD",
        help="Filter by keywords. Prefix with + (or nothing) to require, - to exclude. "
             "e.g. --keywords +markscheme -questions paper2",
    )
    filt.add_argument(
        "--years", nargs="+", type=int, metavar="YEAR",
        help="Whitelist specific years (OR logic). e.g. --years 2019 2020 2021",
    )
    filt.add_argument(
        "--year-range", nargs=2, type=int, metavar=("FROM", "TO"),
        help="Keep only PDFs whose year is within FROM..TO inclusive. "
             "Can be combined with --years (both constraints must pass).",
    )

    return ap


def main():
    ap = _build_parser()
    args = ap.parse_args()

    year_set = set(args.years) if args.years else None
    year_from = year_to = None
    if args.year_range:
        year_from, year_to = sorted(args.year_range)

    print(f"Scraping {args.url} ...")
    try:
        links = scrape_links(args.url)
    except Exception as e:
        print(f"Could not scrape the page: {e}")
        sys.exit(1)

    if not links:
        print("No PDF links found. The page may load links via JavaScript, "
              "or the URL is wrong.")
        sys.exit(1)

    total = len(links)
    links, dropped = apply_filters(
        links,
        keywords=args.keywords,
        year_set=year_set,
        year_from=year_from,
        year_to=year_to,
    )

    slug = page_slug(args.url)

    # Build a human-readable filter summary
    filter_parts = []
    if args.keywords:
        must_have, must_not_have = parse_keywords(args.keywords)
        if must_have:
            filter_parts.append("require: " + ", ".join(f'"{k}"' for k in must_have))
        if must_not_have:
            filter_parts.append("exclude: " + ", ".join(f'"{k}"' for k in must_not_have))
    if year_set:
        filter_parts.append("years: " + ", ".join(str(y) for y in sorted(year_set)))
    if args.year_range:
        filter_parts.append(f"year-range: {year_from}–{year_to}")

    if filter_parts:
        print("Filters: " + " | ".join(filter_parts))
        print(f"Matched {len(links)} of {total} PDF(s) ({dropped} filtered out). "
              f"Organising by '{args.organise}'.\n")
    else:
        print(f"Found {total} PDF(s). Organising by '{args.organise}'.\n")

    if not links:
        print("No PDFs matched the filters.")
        sys.exit(0)

    ok = skipped = failed = 0
    current = None
    for section, label, pdf in links:
        dest = target_path(args.output, slug, section, pdf, args.organise)
        if section != current:
            current = section
            print(f"[{section}]")
        if args.dry_run:
            print(f"  would save -> {dest}")
            continue
        status = download(pdf, dest, args.delay)
        print(f"  {label[:55]:<55} {status}")
        if status == "ok":
            ok += 1
        elif status.startswith("skip"):
            skipped += 1
        else:
            failed += 1

    if not args.dry_run:
        print(f"\nDone. {ok} downloaded, {skipped} skipped, {failed} failed. "
              f"Saved under '{args.output}/'.")
