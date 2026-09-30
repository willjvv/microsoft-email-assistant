import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from email_labeler.auth import get_access_token
from email_labeler.classifier import GeminiFolderSorter
from email_labeler.graph import GraphClient
from email_labeler.config import (
    FOLDERS_FILE,
    PROCESSED_FILE,
    load_folders,
    save_folders,
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


def configure_folders():
    current = load_folders()

    print("\nCurrent folders:")
    for i, folder in enumerate(current, 1):
        print(f"  {i}. {folder}")

    print("\nEnter the folders you want Gemini to sort into.")
    print("Example: Client, Personal, Finance, Newsletter, Urgent")
    raw = input("Folders (comma-separated): ").strip()

    if not raw:
        print("No changes made.")
        return

    folders = []
    for item in raw.split(","):
        item = item.strip()
        if item and item not in folders:
            folders.append(item)

    if not folders:
        print("Please provide at least one folder.")
        return

    save_folders(folders)
    print(f"\nSaved {len(folders)} folders to {FOLDERS_FILE.name}.")


def sort_recent_emails():
    folders = load_folders()

    if not folders:
        print("You need at least one folder. Choose option 1 first.")
        return

    token = get_access_token()
    graph = GraphClient(token)
    sorter = GeminiFolderSorter()

    limit = int(os.getenv("EMAIL_LIMIT", "25"))
    print(f"\nFetching up to {limit} recent inbox emails...")

    messages = graph.get_inbox_messages(limit=limit)

    if not messages:
        print("No messages found.")
        return

    folder_ids = graph.ensure_sorted_folders(folders)
    processed = load_processed()

    print(f"Found {len(messages)} messages.")
    print("Gemini will sort messages that have not been processed.")
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
            result = sorter.choose_folder(
                sender=sender,
                subject=subject,
                body=message.get("bodyPreview", ""),
                folders=folders,
            )

            folder = result.folder

            if folder not in folders:
                print(f"    Gemini returned invalid folder: {folder}")
                failed += 1
                continue

            print(
                f"    → Sorted/{folder} "
                f"(confidence {result.confidence:.0%})"
            )

            # Only move messages when the destination is reasonably clear.
            if result.confidence < 0.70:
                print("    Skipped: confidence below 70%.")
                processed.add(message_id)
                continue

            graph.move_message(message_id, folder_ids[folder])
            processed.add(message_id)
            changed += 1
            print("    Moved.")

        except Exception as exc:
            failed += 1
            print(f"    ERROR: {exc}")

    save_processed(processed)

    print("\nDone.")
    print(f"  Moved: {changed}")
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
        print(" Microsoft + Gemini Email Sorter")
        print("========================================")
        print("1. Configure folders")
        print("2. Sort recent inbox emails")
        print("3. Show folders")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            configure_folders()
        elif choice == "2":
            sort_recent_emails()
        elif choice == "3":
            print("\nFolders under Sorted:")
            for folder in load_folders():
                print(f"  - Sorted/{folder}")
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
