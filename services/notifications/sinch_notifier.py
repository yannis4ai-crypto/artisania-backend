import httpx

from config import settings

SINCH_SEND_URL_TEMPLATE = "https://sms.api.sinch.com/xms/v1/{service_plan_id}/batches"


async def send_sms(*, to: str, body: str) -> None:
    if not settings.sinch_api_key:
        raise RuntimeError("SINCH_API_KEY manquant — configurer .env avant l'envoi")
    url = SINCH_SEND_URL_TEMPLATE.format(service_plan_id=settings.sinch_service_plan_id)
    payload = {"to": [to], "from": settings.sinch_sender_number, "body": body}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {settings.sinch_api_key}"},
        )
        response.raise_for_status()
