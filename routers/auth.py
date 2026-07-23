from fastapi import APIRouter, HTTPException

from services.auth.magic_link import generate_token, verify_token
from services.notifications.mailjet_notifier import send_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-link")
async def request_link(email: str):
    token = generate_token(email)
    # TODO : construire l'URL absolue une fois le domaine de prod connu.
    link = f"/auth/verify?token={token}"
    await send_email(
        to=email,
        subject="Votre lien de connexion",
        body=f"Cliquez pour vous connecter : {link}",
    )
    return {"status": "sent"}


@router.get("/verify")
async def verify(token: str):
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Lien invalide ou expiré")
    # TODO : créer la session par device une fois le schéma étendu (cf CLAUDE.md §6).
    return {"email": email, "status": "verified"}
