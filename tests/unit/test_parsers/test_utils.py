from player_availability.parsers.utils import clean_html, normalize_whitespace


def test_clean_html_strips_tags() -> None:
    html = "<p>Player A is <strong>injured</strong>.</p>"
    result = clean_html(html)
    assert result == "Player A is injured."


def test_clean_html_decodes_entities() -> None:
    html = "<p>Dhoni &amp; Kohli are out.</p>"
    result = clean_html(html)
    assert result == "Dhoni & Kohli are out."


def test_clean_html_nested_tags() -> None:
    html = "<div><p><a href='x'>MS Dhoni</a> suffers <em>knee injury</em>.</p></div>"
    result = clean_html(html)
    assert result == "MS Dhoni suffers knee injury."


def test_clean_html_empty_string() -> None:
    assert clean_html("") == ""


def test_clean_html_no_html() -> None:
    assert clean_html("plain text") == "plain text"


def test_clean_html_whitespace_collapsed() -> None:
    html = "<p>   Player    X   </p>"
    result = clean_html(html)
    assert result == "Player X"


def test_normalize_whitespace_collapses_spaces() -> None:
    assert normalize_whitespace("a   b    c") == "a b c"


def test_normalize_whitespace_strips_outer() -> None:
    assert normalize_whitespace("  hello world  ") == "hello world"


def test_normalize_whitespace_newlines() -> None:
    assert normalize_whitespace("line1\nline2\n\nline3") == "line1 line2 line3"


def test_normalize_whitespace_empty() -> None:
    assert normalize_whitespace("") == ""


def test_normalize_whitespace_tabs() -> None:
    assert normalize_whitespace("a\tb\tc") == "a b c"
