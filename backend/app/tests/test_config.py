from app.config import Settings

# --- Tests for GEMINI_API_KEYS and OPENROUTER_API_KEYS ---

def test_parse_api_keys_valid_json():
    # Valid JSON string representation of a list
    settings = Settings(GEMINI_API_KEYS='["key1", "key2"]')
    assert settings.GEMINI_API_KEYS == ["key1", "key2"]

def test_parse_api_keys_invalid_json_fallback():
    # Invalid JSON string (comma separated) triggers fallback
    settings = Settings(GEMINI_API_KEYS="key1, key2, key3")
    assert settings.GEMINI_API_KEYS == ["key1", "key2", "key3"]

    # Trailing commas and spaces
    settings = Settings(GEMINI_API_KEYS="key1, , key2, ")
    assert settings.GEMINI_API_KEYS == ["key1", "key2"]

def test_parse_api_keys_empty_string():
    # Empty string should return an empty list
    settings = Settings(GEMINI_API_KEYS="")
    assert settings.GEMINI_API_KEYS == []

    # Whitespace string should return an empty list
    settings = Settings(GEMINI_API_KEYS="   ")
    assert settings.GEMINI_API_KEYS == []

def test_parse_api_keys_list():
    # Passing an actual list directly
    settings = Settings(GEMINI_API_KEYS=["key1", "key2"])
    assert settings.GEMINI_API_KEYS == ["key1", "key2"]


# --- Tests for CORS_ORIGINS ---

def test_parse_cors_origins_valid_json():
    # Valid JSON string representation of a list
    settings = Settings(CORS_ORIGINS='["http://localhost:3000", "http://example.com"]')
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://example.com"]

def test_parse_cors_origins_invalid_json_fallback():
    # Invalid JSON string triggers fallback to wrapping the string in a list
    settings = Settings(CORS_ORIGINS="http://example.com")
    assert settings.CORS_ORIGINS == ["http://example.com"]

def test_parse_cors_origins_list():
    # Passing an actual list directly
    settings = Settings(CORS_ORIGINS=["http://localhost:3000"])
    assert settings.CORS_ORIGINS == ["http://localhost:3000"]
