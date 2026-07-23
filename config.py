from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Aucun des 3 candidats (Artisia/Artisania/Appui) n'est validé par le CPI
    # (cf CLAUDE.md §2). Ne jamais coder un nom de marque en dur ailleurs que
    # via ce champ.
    product_name: str = "NOM_NON_TRANCHE"

    api_port: int = 8000

    database_url: str = "postgresql://localhost/artisania"

    mailjet_api_key: str = ""
    mailjet_api_secret: str = ""
    mailjet_sender_email: str = ""

    sinch_api_key: str = ""
    sinch_service_plan_id: str = ""
    sinch_sender_number: str = ""

    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    google_maps_api_key: str = ""

    # Lien magique — secret HMAC de signature des tokens, distinct par env.
    magic_link_secret: str = "CHANGE_ME"
    magic_link_ttl_minutes: int = 15


settings = Settings()
