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

    def test_campus_information_pages_render_as_separate_pages(self):
        pages = {
            "/campus/infrastructure": b"Infrastructure",
            "/campus/child-development": b"Student Development",
            "/campus/education-impact": b"Education Impact",
            "/campus/our-founders": b"Our Founders",
            "/campus/management": b"CMS Management",
        }
        for path, expected_title in pages.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected_title, response.data)
                self.assertIn(b"Back to About Campus", response.data)

    def test_campus_pages_include_deeper_content_and_homepage_destinations(self):
        infra = self.client.get("/campus/infrastructure")
        child = self.client.get("/campus/child-development")
        home = self.client.get("/")
        self.assertIn(b'id="learning-spaces"', infra.data)
        self.assertIn(b'id="student-development"', child.data)
        self.assertIn(b"Robotics and Artificial Intelligence Lab", infra.data)
        self.assertIn(b"Each One", child.data)
        self.assertIn(b"/campus/infrastructure#learning-spaces", home.data)
        self.assertIn(b"/campus/child-development#student-development", home.data)
        self.assertIn(b"Academic Milestones", home.data)
        self.assertIn(b"Digital Campus", home.data)

    def test_unknown_campus_information_page_returns_404(self):
        response = self.client.get("/campus/not-a-page")
        self.assertEqual(response.status_code, 404)

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


    @patch.object(app_module, "select_rows", return_value=[])
    def test_technova_page_renders_without_cloud_database(self, _select_rows):
        response = self.client.get("/technova")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"TECHNOVA", response.data)

    def test_portal_marks_roles_and_notices_as_demo_content(self):
        response = self.client.get("/portal")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"DEMO ENVIRONMENT", response.data)
        self.assertIn(b"SAMPLE CAMPUS BULLETIN", response.data)
        self.assertIn(b"aria-controls=\"workspacePanel\"", response.data)

    def test_public_event_data_endpoint_returns_competitions(self):
        response = self.client.get("/api/data")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload.get("events"))


    @patch.object(app_module, "select_rows", return_value=[{"title": "Campus test notice", "body": "A sample campus update."}])
    def test_homepage_displays_published_announcements(self, _select_rows):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Campus test notice", response.data)
        self.assertIn(b"A sample campus update.", response.data)


if __name__ == "__main__":
    unittest.main()
