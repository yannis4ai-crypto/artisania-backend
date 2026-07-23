import unittest

from fastapi.testclient import TestClient

from main import app


class HealthTests(unittest.TestCase):
    def test_health_ok(self):
        with TestClient(app) as client:
            response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
