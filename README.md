# Microsoft + Gemini Email Sorter MVP

A small Python desktop/console application that:

1. Signs into Microsoft 365 / Outlook using Microsoft Graph.
2. Reads recent messages from your Inbox.
3. Sends the subject, sender, and body preview to Google Gemini.
4. Asks Gemini to choose one of your configured folder names.
5. Moves the Outlook message into that folder under `Sorted`.
6. Remembers processed message IDs so repeated runs do not sort the same messages again.

## Requirements

- Python 3.10+
- A Microsoft account with an Outlook/Exchange mailbox
- A Google Gemini API key
- A Microsoft Entra App Registration

Microsoft Graph uses delegated `Mail.ReadWrite` permission for this MVP.

## 1. Create the Microsoft app

Open Microsoft Entra admin center and create an App Registration.

For a desktop/public-client app:

- Create a new App Registration.
- Copy the **Application (client) ID**.
- Under API permissions, add Microsoft Graph delegated permissions:
  - `User.Read`
  - `Mail.ReadWrite`
- Enable public client flows / mobile and desktop flows if your tenant presents that option.

The app does not request `Mail.Send`.

## 2. Get a Gemini API key

Create a Gemini API key through Google AI Studio.

## 3. Configure the program

Copy:

    .env.example

to:

    .env

Then fill in:

    GEMINI_API_KEY=...
    MICROSOFT_CLIENT_ID=...
    MICROSOFT_TENANT_ID=common

Do not commit `.env` to Git.

## 4. Install

Windows:

    py -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

macOS/Linux:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## 5. Run

    python main.py

The first run gives you:

    1. Configure folders
    2. Sort recent inbox emails
    3. Show folders
    0. Exit

Choose **1** and enter the folder names you want Gemini to use. The app creates
`Sorted` in your mailbox and creates one subfolder beneath it for each name.

For example:

    Client, Personal, Finance, Newsletter, Scheduling, Urgent, Other

Then choose **2**. Messages with confidence of at least 70% are moved into the
matching `Sorted/<folder>` subfolder.

The first Microsoft authentication will display a sign-in/device-code flow. After authentication, the app reads recent Inbox messages and asks Gemini to classify them.

## Safety behavior

- Only messages returned by the Inbox query are considered.
- Only messages that have not previously been recorded in `processed.json` are classified.
- The app requires Gemini confidence >= 70% before moving a message.
- Messages are moved out of the Inbox into a subfolder under `Sorted`.
- The program never sends email.
- The Microsoft access token is cached locally in `msal_token_cache.json`.

## Important privacy note

Email content is being sent to the Gemini API for classification. Do not use this MVP with sensitive mail until you have reviewed Google's Gemini API data/privacy terms and your own obligations.

## Resetting the app

To make the program reconsider previously processed messages:

Delete:

    processed.json

To force a fresh Microsoft sign-in:

Delete:

    msal_token_cache.json

## Next logical upgrades

- GUI
- Dry-run / preview mode
- Per-folder descriptions
- Rules before Gemini
- Confidence threshold setting
- Process only unread messages
- Process a selectable number of messages
- Outlook folder selection
- Classification history
- Retry/rate-limit handling
- Better HTML-body extraction
- Background scheduled operation
