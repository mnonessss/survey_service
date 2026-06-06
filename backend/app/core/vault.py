import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_secret(key: str, *, vault_path: str | None = None) -> str:
    """Читает секрет из HashiCorp Vault (KV v2) или из переменных окружения."""
    env_key = key.upper()
    if settings.VAULT_ADDR and settings.VAULT_TOKEN and vault_path:
        try:
            import hvac

            client = hvac.Client(url=settings.VAULT_ADDR, token=settings.VAULT_TOKEN)
            mount = settings.VAULT_MOUNT_POINT
            secret_path = vault_path.strip("/")
            read_path = secret_path.split("/", 1)
            if len(read_path) == 2:
                mount_point, path = read_path[0], read_path[1]
            else:
                mount_point, path = mount, secret_path

            response = client.secrets.kv.v2.read_secret_version(path=path, mount_point=mount_point)
            data = response["data"]["data"]
            if key in data:
                return str(data[key])
            if env_key in data:
                return str(data[env_key])
        except Exception as exc:
            logger.warning("Vault read failed for %s: %s", vault_path, exc)

    value = os.getenv(env_key, "")
    if not value and hasattr(settings, env_key):
        value = getattr(settings, env_key, "") or ""
    return str(value)
