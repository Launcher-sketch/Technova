import unittest
from unittest.mock import patch

import app as app_module


class CampusSiteSmokeTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = app_module.app.test_client()

    @patch.object(app_module, "select_rows", return_value=[])
    def test_homepage_renders_without_cloud_database(self, _select_rows):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Discover. Experience.", response.data)

    def test_core_pages_render(self):
        for path in ("/about", "/portal", "/celesta", "/academic-results", "/sports", "/cmsmun", "/contact"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_chat_rejects_empty_message_gracefully(self):
        response = self.client.post("/api/chat", json={"message": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["reply"], "Please enter a question.")

    def test_technova_schedule_uses_official_data(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "schedule", "page_context": "/technova"},
        )
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("TECHNOVA 2026", payload["reply"])
        self.assertTrue(payload.get("table", {}).get("rows"))

    def test_technova_generic_venue_query_does_not_guess(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "where is it", "page_context": "/technova"},
        )
        payload = response.get_json()
        self.assertIn("Which competition", payload["reply"])
        self.assertEqual(payload["table"]["headers"], ["Competition", "Venue"])


if __name__ == "__main__":
    unittest.main()
