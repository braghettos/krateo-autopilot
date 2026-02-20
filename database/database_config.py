import logging
from pydantic import SecretStr
from pydantic_settings import BaseSettings

# Configure logging
log = logging.getLogger(__name__)

class DatabaseConfig(BaseSettings):
    cluster_name: str | None = None
    db_username: str | None = None
    db_password: SecretStr | None = None
    db_name: str | None = None
    db_port: int = 5432
    sqlite_session_uri: str = "sqlite:///./sessions.db"

    @property
    def _is_postgres_configured(self) -> bool:
        return all([self.cluster_name, self.db_username, self.db_password, self.db_name])

    def get_session_service_uri(self) -> str:
        if self._is_postgres_configured:
            db_host = f"{self.cluster_name}-rw"
            password = self.db_password.get_secret_value()
            uri = (
                f"postgresql+asyncpg://{self.db_username}:{password}"
                f"@{db_host}:{self.db_port}/{self.db_name}"
            )
            log.info(f"Using PostgreSQL session service at {db_host}:{self.db_port}/{self.db_name}")
            return uri

        log.info("Using local SQLite session service")
        return self.sqlite_session_uri