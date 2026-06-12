import hashlib
import hmac
from base64 import b64encode
from urllib.parse import parse_qsl, urlencode, urlparse


def verify_vk_launch_signature(data: dict, secret_key: str) -> bool:
    """Проверка подписи параметров запуска VK Mini App (алгоритм dev.vk.com)."""
    sign_from_vk = data.get("sign")
    if not sign_from_vk:
        return False

    vk_keys = sorted(k for k in data if k.startswith("vk_"))
    if not vk_keys:
        return False

    ordered = {k: str(data[k]) for k in vk_keys if data[k] is not None}
    sign_params_query = urlencode(ordered)

    hash_code = b64encode(
        hmac.new(
            secret_key.encode("utf-8"),
            sign_params_query.encode("utf-8"),
            hashlib.sha256,
        ).digest(),
    ).decode("utf-8")

    if hash_code.endswith("="):
        hash_code = hash_code[:-1]

    expected_sign = hash_code.replace("+", "-").replace("/", "_")
    return hmac.compare_digest(expected_sign, str(sign_from_vk))


def verify_vk_launch_signature_from_url(url: str, secret_key: str) -> bool:
    """Проверка подписи из полного URL (hash или query)."""
    parsed = urlparse(url)
    raw = parsed.query or parsed.fragment
    if not raw:
        return False
    query = dict(parse_qsl(raw, keep_blank_values=True))
    return verify_vk_launch_signature(query, secret_key)
