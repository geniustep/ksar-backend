from app.core.security import (
    normalize_arabic,
    generate_duplicate_hash,
    generate_otp,
    hash_otp,
    verify_otp,
    create_access_token,
    decode_token,
)


def test_normalize_arabic():
    # Remove diacritics
    assert normalize_arabic("بِسْمِ") == "بسم"

    # Normalize alef variants
    text = normalize_arabic("إبراهيم أحمد آل")
    assert "إ" not in text
    assert "أ" not in text
    assert "آ" not in text

    # Normalize taa marbuta
    assert normalize_arabic("مدرسة") == "مدرسه"

    # Remove extra whitespace
    assert normalize_arabic("حي   السلام") == "حي السلام"


def test_generate_duplicate_hash():
    hash1 = generate_duplicate_hash("+212600000001", "food", "حي السلام")
    hash2 = generate_duplicate_hash("+212600000001", "food", "حي السلام")
    hash3 = generate_duplicate_hash("+212600000001", "medicine", "حي السلام")

    assert hash1 == hash2  # Same inputs produce same hash
    assert hash1 != hash3  # Different category produces different hash
    assert len(hash1) == 64  # SHA256 hex length


def test_otp_generation():
    otp = generate_otp(6)
    assert len(otp) == 6
    assert otp.isdigit()


def test_otp_hashing_and_verification():
    otp = "123456"
    hashed = hash_otp(otp)
    assert verify_otp("123456", hashed)
    assert not verify_otp("654321", hashed)


def test_jwt_token_creation_and_decoding():
    data = {"sub": "test-user-id", "role": "resident"}
    token = create_access_token(data)
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "test-user-id"
    assert payload["role"] == "resident"
    assert payload["type"] == "access"


def test_invalid_token_decoding():
    result = decode_token("invalid.token.here")
    assert result is None
