from utils.text_cleaner import clean_comment


def test_clean_comment_preserves_unicode_and_normalizes_spaces():
    result = clean_comment("  Hello   दुनिया  ✨\nfriend! ")
    assert result["original_text"].startswith("  ")
    assert result["cleaned_text"] == "Hello दुनिया ✨ friend!"


def test_clean_comment_handles_empty_values():
    assert clean_comment(None)["cleaned_text"] == ""
    assert clean_comment("   ")["cleaned_text"] == ""
