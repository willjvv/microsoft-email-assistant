import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphClient:
    def __init__(self, access_token):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        })

    def get_inbox_messages(self, limit=25):
        url = f"{GRAPH_BASE}/me/mailFolders/inbox/messages"

        params = {
            "$top": limit,
            "$select": (
                "id,subject,from,receivedDateTime,"
                "bodyPreview,categories,isRead"
            ),
            "$orderby": "receivedDateTime DESC",
        }

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        return response.json().get("value", [])

    def add_category(self, message_id, category):
        url = f"{GRAPH_BASE}/me/messages/{message_id}"

        # Preserve categories already on the message.
        current = self._get_message_categories(message_id)

        if category in current:
            return

        categories = current + [category]

        response = self.session.patch(
            url,
            json={"categories": categories},
            timeout=30,
        )
        response.raise_for_status()

    def _get_message_categories(self, message_id):
        url = f"{GRAPH_BASE}/me/messages/{message_id}"

        response = self.session.get(
            url,
            params={"$select": "categories"},
            timeout=30,
        )
        response.raise_for_status()

        return response.json().get("categories", [])
