import httpx

from config import settings

MAILJET_SEND_URL = "https://api.mailjet.com/v3.1/send"


async def send_email(*, to: str, subject: str, body: str) -> None:
    if not settings.mailjet_api_key:
        raise RuntimeError("MAILJET_API_KEY manquant — configurer .env avant l'envoi")
    payload = {
        "Messages": [
            {
                "From": {"Email": settings.mailjet_sender_email},
                "To": [{"Email": to}],
                "Subject": subject,
                "TextPart": body,
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            MAILJET_SEND_URL,
            json=payload,
            auth=(settings.mailjet_api_key, settings.mailjet_api_secret),
        )
        response.raise_for_status()
