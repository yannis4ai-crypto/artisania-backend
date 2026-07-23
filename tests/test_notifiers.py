import unittest
from unittest.mock import AsyncMock, patch

from config import settings
from services.notifications import mailjet_notifier, sinch_notifier


class MailjetNotifierTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_email_requires_api_key(self):
        with patch.object(settings, "mailjet_api_key", ""):
            with self.assertRaises(RuntimeError):
                await mailjet_notifier.send_email(to="a@b.fr", subject="x", body="y")

    async def test_send_email_calls_api_without_real_network(self):
        with (
            patch.object(settings, "mailjet_api_key", "key"),
            patch.object(settings, "mailjet_api_secret", "secret"),
            patch.object(settings, "mailjet_sender_email", "from@artisania.fr"),
            patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        ):
            mock_post.return_value.raise_for_status = lambda: None
            await mailjet_notifier.send_email(to="a@b.fr", subject="x", body="y")
            mock_post.assert_called_once()


class SinchNotifierTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_sms_requires_api_key(self):
        with patch.object(settings, "sinch_api_token", ""):
            with self.assertRaises(RuntimeError):
                await sinch_notifier.send_sms(to="+33600000000", body="y")

    async def test_send_sms_calls_api_without_real_network(self):
        with (
            patch.object(settings, "sinch_api_token", "key"),
            patch.object(settings, "sinch_service_plan_id", "plan"),
            patch.object(settings, "sinch_sender_number", "+33700000000"),
            patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        ):
            mock_post.return_value.raise_for_status = lambda: None
            await sinch_notifier.send_sms(to="+33600000000", body="y")
            mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
