import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from email_labeler.auth import get_access_token
from email_labeler.classifier import GeminiClassifier
from email_labeler.graph import GraphClient
from email_labeler.config import (
    CATEGORIES_FILE,
    PROCESSED_FILE,
    load_categories,
    save_categories,
)


def load_processed():
    if not PROCESSED_FILE.exists():
        return set()
    try:
        data = json.loads(PROCESSED_FILE.read_text(encoding="utf-8"))
        return set(data)
    except (json.JSONDecodeError, OSError):
        return set()


def save_processed(ids):
    PROCESSED_FILE.write_text(
        json.dumps(sorted(ids), indent=2),
        encoding="utf-8",
    )


def configure_categories():
    current = load_categories()

    print("\nCurrent categories:")
    for i, category in enumerate(current, 1):
        print(f"  {i}. {category}")

    print("\nEnter the categories you want Gemini to use.")
    print("Example: Client, Personal, Finance, Newsletter, Urgent")
    raw = input("Categories (comma-separated): ").strip()

    if not raw:
        print("No changes made.")
        return

    categories = []
    for item in raw.split(","):
        item = item.strip()
        if item and item not in categories:
            categories.append(item)

    if len(categories) < 2:
        print("Please provide at least two categories.")
        return

    save_categories(categories)
    print(f"\nSaved {len(categories)} categories to {CATEGORIES_FILE.name}.")


def run_labeling():
    categories = load_categories()

    if len(categories) < 2:
        print("You need at least two categories. Choose option 1 first.")
        return

    token = get_access_token()
    graph = GraphClient(token)
    classifier = GeminiClassifier()

    limit = int(os.getenv("EMAIL_LIMIT", "25"))
    print(f"\nFetching up to {limit} recent inbox emails...")

    messages = graph.get_inbox_messages(limit=limit)

    if not messages:
        print("No messages found.")
        return

    processed = load_processed()

    print(f"Found {len(messages)} messages.")
    print("Gemini will classify messages that have not been processed.")
    print("Press Ctrl+C to stop.\n")

    changed = 0
    skipped = 0
    failed = 0

    for index, message in enumerate(messages, 1):
        message_id = message.get("id")
        subject = message.get("subject") or "(no subject)"
        sender = (
            message.get("from", {})
            .get("emailAddress", {})
            .get("address", "")
        )

        if not message_id:
            continue

        if message_id in processed:
            skipped += 1
            continue

        print(f"[{index}/{len(messages)}] {subject}")
        print(f"    From: {sender}")

        try:
            result = classifier.classify(
                sender=sender,
                subject=subject,
                body=message.get("bodyPreview", ""),
                categories=categories,
            )

            category = result.category

            if category not in categories:
                print(f"    Gemini returned invalid category: {category}")
                failed += 1
                continue

            print(
                f"    → {category} "
                f"(confidence {result.confidence:.0%})"
            )

            # Only apply the label when confidence is reasonably high.
            # You can lower this threshold later if desired.
            if result.confidence < 0.70:
                print("    Skipped: confidence below 70%.")
                processed.add(message_id)
                continue

            graph.add_category(message_id, category)
            processed.add(message_id)
            changed += 1
            print("    Labeled.")

        except Exception as exc:
            failed += 1
            print(f"    ERROR: {exc}")

    save_processed(processed)

    print("\nDone.")
    print(f"  Labeled: {changed}")
    print(f"  Already processed: {skipped}")
    print(f"  Failed: {failed}")


def main():
    load_dotenv()

    if not os.getenv("GEMINI_API_KEY"):
        print("Missing GEMINI_API_KEY. Copy .env.example to .env and configure it.")
        sys.exit(1)

    if not os.getenv("MICROSOFT_CLIENT_ID"):
        print("Missing MICROSOFT_CLIENT_ID. Copy .env.example to .env and configure it.")
        sys.exit(1)

    while True:
        print("\n========================================")
        print(" Microsoft + Gemini Email Labeler")
        print("========================================")
        print("1. Configure categories")
        print("2. Label recent inbox emails")
        print("3. Show categories")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            configure_categories()
        elif choice == "2":
            run_labeling()
        elif choice == "3":
            print("\nCategories:")
            for category in load_categories():
                print(f"  - {category}")
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
