from app.security.vk_mini_app import verify_vk_launch_signature, verify_vk_launch_signature_from_url

OFFICIAL_URL = (
    "https://example.com/?vk_user_id=494075&vk_app_id=6736218&vk_is_app_user=1"
    "&vk_are_notifications_enabled=1&vk_language=ru&vk_access_token_settings="
    "&vk_platform=android&sign=htQFduJpLxz7ribXRZpDFUH-XEUhC9rBPTJkjUFEkRA"
)
OFFICIAL_SECRET = "wvl68m4dR1UpLrVRli"


def test_verify_official_vk_example():
    assert verify_vk_launch_signature_from_url(OFFICIAL_URL, OFFICIAL_SECRET)


def test_verify_rejects_wrong_secret():
    assert not verify_vk_launch_signature_from_url(OFFICIAL_URL, "wrong-secret")


def test_verify_rejects_tampered_user_id():
    data = {
        "vk_user_id": 999999,
        "vk_app_id": 6736218,
        "vk_is_app_user": 1,
        "vk_are_notifications_enabled": 1,
        "vk_language": "ru",
        "vk_access_token_settings": "",
        "vk_platform": "android",
        "sign": "htQFduJpLxz7ribXRZpDFUH-XEUhC9rBPTJkjUFEkRA",
    }
    assert not verify_vk_launch_signature(data, OFFICIAL_SECRET)


def test_verify_rejects_missing_sign():
    data = {"vk_user_id": 494075, "vk_app_id": 6736218}
    assert not verify_vk_launch_signature(data, OFFICIAL_SECRET)
