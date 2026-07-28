"""Orchestrate scrape → save → optional email alert."""

from app.alerts import send_price_alert
from app.db import (
    add_history,
    get_product_by_url,
    init_db,
    list_products,
    upsert_product,
)
from app.scraper import scrape_product


def check_product(url: str, send_alerts: bool = True) -> dict:
    """Scrape one URL, save it, and alert on price change.

    Always appends a history row.
    Email only if there was a previous price and it differs.
    """
    init_db()
    previous = get_product_by_url(url)
    scraped = scrape_product(url)

    old_price = previous["last_price"] if previous else None
    new_price = scraped["price"]

    product = upsert_product(
        url=url,
        title=scraped["title"],
        price=new_price,
        availability=scraped["availability"],
    )
    history = add_history(
        product_id=product["id"],
        price=new_price,
        availability=scraped["availability"],
    )

    price_changed = (
        old_price is not None
        and new_price is not None
        and float(old_price) != float(new_price)
    )

    alert_sent = False
    if send_alerts and price_changed:
        alert_sent = send_price_alert(
            title=scraped["title"],
            url=url,
            old_price=float(old_price),
            new_price=float(new_price),
        )

    return {
        "product": product,
        "history": history,
        "scraped": scraped,
        "price_changed": price_changed,
        "old_price": old_price,
        "new_price": new_price,
        "alert_sent": alert_sent,
    }


def check_all(send_alerts: bool = True) -> list:
    """Re-scrape every tracked product. One failure won't stop the rest."""
    init_db()
    results = []
    for product in list_products():
        try:
            results.append(
                check_product(product["url"], send_alerts=send_alerts)
            )
        except Exception as exc:
            results.append(
                {
                    "product": product,
                    "error": str(exc),
                    "price_changed": False,
                    "alert_sent": False,
                }
            )
    return results