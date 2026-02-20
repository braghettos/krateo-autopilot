import logging
from pydantic import SecretStr
from pydantic_settings import BaseSettings

log = logging.getLogger(__name__)

class DatabaseConfig(BaseSettings):
    """Configuration for database connection"""
    
    cluster_name: str | None = None
    """CloudNativePG cluster name"""
    
    db_username: str | None = None
    """Database username"""
    
    db_password: SecretStr | None = None
    """Database password"""
    
    db_name: str | None = None
    """Database name"""
    
    db_port: int = 5432
    """Database port. Must use a read-write service if using CloudNativePG"""
    
    sqlite_session_uri: str = "sqlite:///./sessions.db"
    """Fallback SQLite URI for local development or if PostgreSQL config is incomplete"""

    @property
    def _is_postgres_configured(self) -> bool:
        """Check if all required PostgreSQL configuration is present"""
        return all([self.cluster_name, self.db_username, self.db_password, self.db_name])

    def get_session_service_uri(self) -> str:
        """Returns the appropriate session service URI based on the configuration.
        
        Uses CloudnativePG if all required PostgreSQL configuration is provided, otherwise falls back to in memory SQLite.
        """
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