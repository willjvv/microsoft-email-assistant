import unittest
from unittest.mock import Mock

from email_labeler.graph import GRAPH_BASE, GraphClient


class GraphClientFolderTests(unittest.TestCase):
    def setUp(self):
        self.client = GraphClient("token")
        self.client.session = Mock()

    def test_ensures_named_folders_under_sorted(self):
        root_response = Mock()
        root_response.json.return_value = {"value": []}
        child_response = Mock()
        child_response.json.return_value = {"value": []}
        created_root = Mock()
        created_root.json.return_value = {"id": "sorted-id"}
        created_child = Mock()
        created_child.json.return_value = {"id": "client-id"}
        self.client.session.get.side_effect = [root_response, child_response]
        self.client.session.post.side_effect = [created_root, created_child]

        folders = self.client.ensure_sorted_folders(["Client"])

        self.assertEqual(folders, {"Client": "client-id"})
        self.client.session.post.assert_any_call(
            f"{GRAPH_BASE}/me/mailFolders",
            json={"displayName": "Sorted"},
            timeout=30,
        )
        self.client.session.post.assert_any_call(
            f"{GRAPH_BASE}/me/mailFolders/sorted-id/childFolders",
            json={"displayName": "Client"},
            timeout=30,
        )

    def test_move_message_posts_destination_folder(self):
        response = Mock()
        self.client.session.post.return_value = response

        self.client.move_message("message-id", "folder-id")

        self.client.session.post.assert_called_once_with(
            f"{GRAPH_BASE}/me/messages/message-id/move",
            json={"destinationId": "folder-id"},
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()