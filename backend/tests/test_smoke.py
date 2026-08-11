from app.core.security import hash_password, verify_password
from app.utils.text import strip_unit_suffix


def test_password_hash_roundtrip():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_strip_unit_suffix():
    assert strip_unit_suffix("猪肉500克") == ("猪肉", "克")
    assert strip_unit_suffix("鸡蛋2个") == ("鸡蛋", "个")
    assert strip_unit_suffix("葱花") == ("葱花", None)
