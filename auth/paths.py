from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "coros-mcp"
ENV_FILE = CONFIG_DIR / ".env"
CREDENTIALS_FILE = CONFIG_DIR / "auth.enc"
