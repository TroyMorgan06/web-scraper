"""Fetch product pages and extract title, price, availability."""

import json
import re

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Ensure frozen-app browser path is configured before Playwright launches
from app import config as _config  # noqa: F401


def parse_price(raw):
    """Turn values like '$19.99' or 19.99 into a float, or None."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)

    text = str(raw).strip()
    if not text:
        return None

    # Remove thousands-commas, then find the first number
    match = re.search(r"[\d.]+", text.replace(",", ""))
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def fetch_html(url: str, timeout_ms: int = 30000) -> str:
    """Open a URL in headless Chromium and return the final HTML."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            # Brief pause for late-loading JS content
            page.wait_for_timeout(1500)
            return page.content()
        finally:
            browser.close()

def _as_list(value):
    """JSON-LD sometimes uses one object, sometimes a list — normalize to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _find_product_nodes(data):
    """Walk JSON and collect dicts that look like schema.org Product."""
    products = []

    def walk(node):
        if isinstance(node, dict):
            types = [str(t).lower() for t in _as_list(node.get("@type"))]
            if any(t == "product" or t.endswith("/product") for t in types):
                products.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return products


def _offer_fields(product: dict):
    """Pull price + availability out of a Product's offers."""
    offers = product.get("offers")
    if offers is None:
        return None, None

    offer = offers[0] if isinstance(offers, list) and offers else offers
    if not isinstance(offer, dict):
        return None, None

    price = parse_price(offer.get("price") or offer.get("lowPrice"))
    availability = offer.get("availability")
    if isinstance(availability, str):
        # https://schema.org/InStock -> InStock
        availability = availability.rstrip("/").split("/")[-1]
    return price, availability


def extract_from_json_ld(soup: BeautifulSoup):
    """Try JSON-LD Product schema. Return dict or None."""
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for script in scripts:
        raw = script.string or script.get_text()
        if not raw or not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        for product in _find_product_nodes(data):
            title = product.get("name")
            price, availability = _offer_fields(product)
            if title or price is not None:
                return {
                    "title": title,
                    "price": price,
                    "availability": availability,
                    "source": "json-ld",
                }
    return None


def extract_from_open_graph(soup: BeautifulSoup):
    """Fallback: meta tags, then common CSS selectors."""

    def meta_content(*keys):
        for key in keys:
            tag = soup.find("meta", property=key) or soup.find(
                "meta", attrs={"name": key}
            )
            if tag and tag.get("content"):
                return tag["content"].strip()
        return None

    title = meta_content("og:title", "twitter:title")
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()

    price = parse_price(
        meta_content("product:price:amount", "og:price:amount", "twitter:data1")
    )

    if price is None:
        price_el = soup.select_one(
            "[itemprop=price], .price_color, .price, .product-price, "
            "#price, .a-price .a-offscreen"
        )
        if price_el:
            price = parse_price(price_el.get("content") or price_el.get_text())

    availability = meta_content("product:availability", "og:availability")
    if not availability:
        avail_el = soup.select_one(
            "[itemprop=availability], .instock.availability, .availability"
        )
        if avail_el:
            availability = " ".join(avail_el.get_text().split())

    if title or price is not None:
        return {
            "title": title,
            "price": price,
            "availability": availability,
            "source": "open-graph",
        }
    return None


def scrape_product(url: str) -> dict:
    """Fetch a URL and return title, price, availability.

    Raises RuntimeError if nothing useful can be extracted.
    """
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    result = extract_from_json_ld(soup) or extract_from_open_graph(soup)
    if result is None:
        raise RuntimeError(
            f"Could not extract product data from {url}. "
            "Page may not expose JSON-LD or recognizable price markup."
        )

    return {
        "url": url,
        "title": result.get("title"),
        "price": result.get("price"),
        "availability": result.get("availability"),
        "source": result.get("source"),
    }