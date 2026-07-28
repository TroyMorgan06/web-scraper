#!/usr/bin/env python3
"""Command-line interface for the Universal Product Tracker."""

import argparse
import sys
from pathlib import Path

from app.config import DATA_DIR
from app.db import get_history, get_product_by_id, init_db, list_products
from app.export import export_history_csv
from app.tracker import check_all, check_product


def cmd_add(args):
    """Track (or refresh) a product URL. No email on add."""
    result = check_product(args.url, send_alerts=False)
    product = result["product"]
    scraped = result["scraped"]
    print(f"Tracked: {product['title'] or product['url']}")
    print(f"  Price: {product['last_price']}")
    print(f"  Availability: {product['availability']}")
    print(f"  Source: {scraped.get('source')}")
    print(f"  Product ID: {product['id']}")
    return 0


def cmd_check(args):
    """Re-scrape one URL or every tracked product."""
    if args.url:
        result = check_product(args.url, send_alerts=not args.no_email)
        _print_check_result(result)
        return 0 if "error" not in result else 1

    results = check_all(send_alerts=not args.no_email)
    if not results:
        print("No products tracked yet. Use: python cli.py add <url>")
        return 0

    errors = 0
    for result in results:
        _print_check_result(result)
        if "error" in result:
            errors += 1
    return 1 if errors else 0


def _print_check_result(result):
    if "error" in result:
        product = result.get("product") or {}
        print(f"ERROR [{product.get('url', '?')}]: {result['error']}")
        return

    product = result["product"]
    print(f"Checked: {product['title'] or product['url']}")
    print(f"  Price: {result['old_price']} -> {result['new_price']}")
    if result["price_changed"]:
        print("  Price changed!")
        if result["alert_sent"]:
            print("  Email alert sent.")
        else:
            print("  Email alert not sent (not configured or skipped).")
    else:
        print("  No price change.")


def cmd_list(args):
    """List tracked products."""
    init_db()
    products = list_products()
    if not products:
        print("No products tracked yet.")
        return 0
    for p in products:
        print(
            f"[{p['id']}] {p['title'] or '(no title)'} | "
            f"${p['last_price']} | {p['availability'] or 'n/a'}"
        )
        print(f"     {p['url']}")
    return 0


def cmd_history(args):
    """Show price history."""
    init_db()
    if args.product_id is not None:
        product = get_product_by_id(args.product_id)
        if product is None:
            print(f"No product with id {args.product_id}")
            return 1
        rows = get_history(args.product_id)
    else:
        rows = get_history()

    if not rows:
        print("No history yet.")
        return 0

    for row in rows:
        print(
            f"{row['scraped_at']} | id={row['product_id']} | "
            f"{row['title'] or row['url']} | ${row['price']} | "
            f"{row['availability'] or 'n/a'}"
        )
    return 0


def cmd_export(args):
    """Export history to CSV."""
    init_db()
    output = Path(args.output) if args.output else DATA_DIR / "history_export.csv"
    path = export_history_csv(output, product_id=args.product_id)
    print(f"Exported to {path}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Universal Product Tracker — scrape, history, alerts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Scrape and start tracking a URL")
    add_p.add_argument("url", help="Product page URL")
    add_p.set_defaults(func=cmd_add)

    check_p = sub.add_parser("check", help="Re-scrape tracked products")
    check_p.add_argument("url", nargs="?", help="Optional single URL")
    check_p.add_argument(
        "--no-email",
        action="store_true",
        help="Do not send email even if price changed",
    )
    check_p.set_defaults(func=cmd_check)

    list_p = sub.add_parser("list", help="List tracked products")
    list_p.set_defaults(func=cmd_list)

    hist_p = sub.add_parser("history", help="Show price history")
    hist_p.add_argument("--product-id", type=int, default=None)
    hist_p.set_defaults(func=cmd_history)

    export_p = sub.add_parser("export", help="Export history to CSV")
    export_p.add_argument("-o", "--output", default=None)
    export_p.add_argument("--product-id", type=int, default=None)
    export_p.set_defaults(func=cmd_export)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())