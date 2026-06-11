import hashlib
import hmac


def verify_vk_launch_signature(data: dict, secret_key: str) -> bool:
    """Проверка подписи параметров запуска VK Mini App (HMAC-SHA256, hex)."""
    payload = {k: v for k, v in data.items() if v is not None}
    sign_from_vk = payload.pop("sign", None)
    if not sign_from_vk:
        return False

    params_to_check = {k: str(v) for k, v in payload.items()}
    msg = "\n".join(f"{key}={params_to_check[key]}" for key in sorted(params_to_check.keys()))

    expected_sign = hmac.new(
        secret_key.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sign, str(sign_from_vk))
