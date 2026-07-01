from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceEntry(BaseModel):
    name: str
    base_url: str
    type: str
    is_active: bool = True


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
        SourceEntry(name="ipl_official", base_url="https://www.iplt20.com/rss/news", type="rss"),
        SourceEntry(name="espn_cricinfo", base_url="https://www.espncricinfo.com/rss/content/story/feeds", type="rss"),
    ]


settings = Settings()
