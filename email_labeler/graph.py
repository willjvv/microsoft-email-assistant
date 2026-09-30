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
                "bodyPreview,isRead"
            ),
            "$orderby": "receivedDateTime DESC",
        }

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        return response.json().get("value", [])

    def ensure_folder(self, display_name, parent_id=None):
        if parent_id:
            collection_url = (
                f"{GRAPH_BASE}/me/mailFolders/{parent_id}/childFolders"
            )
        else:
            collection_url = f"{GRAPH_BASE}/me/mailFolders"

        escaped_name = display_name.replace("'", "''")
        response = self.session.get(
            collection_url,
            params={"$filter": f"displayName eq '{escaped_name}'"},
            timeout=30,
        )
        response.raise_for_status()

        folders = response.json().get("value", [])
        for folder in folders:
            if folder.get("displayName", "").casefold() == display_name.casefold():
                return folder["id"]

        response = self.session.post(
            collection_url,
            json={"displayName": display_name},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["id"]

    def ensure_sorted_folders(self, folder_names):
        sorted_folder_id = self.ensure_folder("Sorted")
        return {
            name: self.ensure_folder(name, parent_id=sorted_folder_id)
            for name in folder_names
        }

    def move_message(self, message_id, destination_folder_id):
        url = f"{GRAPH_BASE}/me/messages/{message_id}/move"
        response = self.session.post(
            url,
            json={"destinationId": destination_folder_id},
            timeout=30,
        )
        response.raise_for_status()
