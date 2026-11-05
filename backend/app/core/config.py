import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base workspace directory & frozen state detection
if getattr(sys, "frozen", False):
    # Running inside a PyInstaller bundle
    # BUNDLE_DIR holds packaged static frontend assets and internal code
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", sys.executable)).resolve()
    # RUNTIME_DIR is alongside the executable (for user's database, logs, thumbnails)
    RUNTIME_DIR = Path(sys.executable).resolve().parent
else:
    # Running in normal development environment
    BUNDLE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    RUNTIME_DIR = BUNDLE_DIR

BASE_DIR = RUNTIME_DIR
DATA_DIR = RUNTIME_DIR / "data"

# Frontend dist resolution
FRONTEND_DIST = BUNDLE_DIR / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = RUNTIME_DIR / "frontend" / "dist"

class Settings(BaseSettings):
    app_name: str = "拾光记"
    app_version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8765
    
    # Path configuration
    base_dir: Path = BASE_DIR
    data_dir: Path = DATA_DIR
    bundle_dir: Path = BUNDLE_DIR
    frontend_dist: Path = FRONTEND_DIST
    photo_root: str = ""
    birth_date: str = ""
    baseline_type: str = "BIRTHDAY"  # BIRTHDAY, ANNIVERSARY, START_DATE, CUSTOM, NONE
    baseline_date: str = ""
    baseline_label: str = ""
    
    # Image resolution settings
    thumbnail_size: int = 480
    preview_size: int = 1600
    
    # DB URL
    @property
    def database_url(self) -> str:
        db_file = self.data_dir / "growing_up.db"
        return f"sqlite:///{db_file.as_posix()}"

    model_config = SettingsConfigDict(
        env_file=str(RUNTIME_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure standard runtime data subdirectories exist
for sub_dir in ["thumbnails", "previews", "cache", "backups", "logs", "config"]:
    (settings.data_dir / sub_dir).mkdir(parents=True, exist_ok=True)
