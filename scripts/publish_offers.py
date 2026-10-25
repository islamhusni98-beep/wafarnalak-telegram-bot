"""Publish due, manually curated Amazon Egypt offers to Telegram."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from telegram_api import send_message


ROOT = Path(__file__).resolve().parents[1]
OFFERS_PATH = ROOT / "data" / "offers.json"
PUBLISHED_PATH = ROOT / "data" / "published.json"
ALLOWED_HOSTS = {"amazon.eg", "www.amazon.eg", "amzn.to"}


def parse_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Offer field {field_name!r} must be an ISO 8601 date-time.")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"Offer field {field_name!r} is not a valid ISO 8601 date-time."
        ) from exc
    if parsed.tzinfo is None:
        raise ValueError(
            f"Offer field {field_name!r} must include a timezone, such as +03:00."
        )
    return parsed


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_published(ids: set[str]) -> None:
    PUBLISHED_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = PUBLISHED_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(sorted(ids), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(PUBLISHED_PATH)


def offer_message(offer: dict[str, object]) -> str:
    title = str(offer.get("title", "")).strip()
    price = str(offer.get("price", "")).strip()
    url = str(offer.get("url", "")).strip()
    if not title or not price or not url:
        raise ValueError("Each offer needs non-empty title, price, and url fields.")

    parsed_url = urlsplit(url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in ALLOWED_HOSTS
        or parsed_url.username
        or parsed_url.password
    ):
        raise ValueError(
            f"Offer URL must be an HTTPS Amazon.eg or amzn.to link: {url}"
        )

    lines = [
        "🔥 عرض جديد من وفرنالك عروض",
        "",
        f"🛍️ {title}",
        f"💰 السعر الحالي: {price}",
    ]

    old_price = str(offer.get("old_price", "")).strip()
    if old_price:
        lines.append(f"قبل الخصم: {old_price}")

    discount = offer.get("discount_percent")
    if discount is not None and str(discount).strip():
        lines.append(f"🏷️ الخصم: {discount}%")

    lines.extend(
        [
            "",
            f"🔗 اطلبه من هنا: {url}",
            "",
            "الأسعار والتوفر قد يتغيران.",
            "قد نحصل على عمولة من المشتريات المؤهلة.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    offers = load_json(OFFERS_PATH, [])
    published = load_json(PUBLISHED_PATH, [])
    if not isinstance(offers, list):
        raise ValueError("data/offers.json must contain a JSON array.")
    if not isinstance(published, list) or not all(
        isinstance(item, str) for item in published
    ):
        raise ValueError("data/published.json must contain an array of offer IDs.")

    published_ids = set(published)
    seen_ids: set[str] = set()
    now = datetime.now(timezone.utc)
    sent_count = 0

    for offer in offers:
        if not isinstance(offer, dict):
            raise ValueError("Every item in data/offers.json must be an object.")

        offer_id = str(offer.get("id", "")).strip()
        if not offer_id:
            raise ValueError("Each offer needs a unique, non-empty id.")
        if offer_id in seen_ids:
            raise ValueError(f"Duplicate offer id: {offer_id}")
        seen_ids.add(offer_id)

        if offer_id in published_ids:
            continue

        publish_at = parse_datetime(offer.get("publish_at"), "publish_at")
        if now < publish_at.astimezone(timezone.utc):
            continue

        expires_at_value = offer.get("expires_at")
        if expires_at_value:
            expires_at = parse_datetime(expires_at_value, "expires_at")
            if now > expires_at.astimezone(timezone.utc):
                print(f"Skipping expired offer {offer_id}.")
                continue

        message = offer_message(offer)
        send_message(message)

        # Save after each successful Telegram response so later offers can continue safely.
        published_ids.add(offer_id)
        save_published(published_ids)
        sent_count += 1
        print(f"Published offer {offer_id}.")

    if sent_count == 0:
        print("No due offers to publish.")


if __name__ == "__main__":
    main()
