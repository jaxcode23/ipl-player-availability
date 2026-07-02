from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceEntry(BaseModel):
    name: str
    base_url: str
    type: str = "rss"
    is_active: bool = True
    mechanism: str = "rss"
    fetch_full_article: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PA_", env_file=".env")

    database_url: str = "sqlite:///data/player_availability.db"
    log_level: str = "INFO"
    db_echo: bool = False

    @property
    def source_registry(self) -> list[SourceEntry]:
        return _default_sources()


def _default_sources() -> list[SourceEntry]:
    return [
        SourceEntry(
            name="rediff_cricket",
            base_url="https://cricket.rediff.com/rss/cricketrss.xml",
            type="rss",
            mechanism="rss",
        ),
        SourceEntry(
            name="google_cricket_news",
            base_url="https://news.google.com/rss/search?q=IPL+2026+player+injury+replacement+ruled+out&hl=en-IN&gl=IN&ceid=IN:en",
            type="rss",
            mechanism="rss",
        ),
    ]


settings = Settings()
