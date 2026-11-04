from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base workspace directory (gallery root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseSettings):
    app_name: str = "Growing Up"
    app_version: str = "2.0.0"
    host: str = "127.0.0.1"
    port: int = 8765
    
    # Path configuration
    base_dir: Path = BASE_DIR
    data_dir: Path = DATA_DIR
    photo_root: str = ""
    birth_date: str = ""
    
    # Image resolution settings
    thumbnail_size: int = 480
    preview_size: int = 1600
    
    # DB URL
    @property
    def database_url(self) -> str:
        db_file = self.data_dir / "growing_up.db"
        return f"sqlite:///{db_file.as_posix()}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure standard runtime data subdirectories exist
for sub_dir in ["thumbnails", "previews", "cache", "backups", "logs", "config"]:
    (settings.data_dir / sub_dir).mkdir(parents=True, exist_ok=True)
