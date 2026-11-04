import json

import pytest

from utils.add_signs import add_signs, normalise

CONFIG = {"classes": ["hello", "iloveyou"], "colors": [[1, 2, 3], [4, 5, 6]]}
PHRASES = 'export const PHRASES = {\n  hello: { en: "Hello" },\n  stop: { en: "Stop" },\n};\nexport const ACTIVE_SIGNS = ["hello", "iloveyou"];\n'


@pytest.fixture
def files(tmp_path):
    cfg, js = tmp_path / "config.json", tmp_path / "phrases.js"
    cfg.write_text(json.dumps(CONFIG))
    js.write_text(PHRASES)
    return cfg, js


def test_normalise():
    assert normalise("Thumbs Up") == "thumbsup"
    assert normalise("  STOP ") == "stop"
    with pytest.raises(ValueError):
        normalise("!!!")


def test_appends_classes_and_colours_in_order(files):
    cfg, js = files
    result = add_signs(["stop", "yes"], cfg, js)
    saved = json.loads(cfg.read_text())
    assert saved["classes"] == ["hello", "iloveyou", "stop", "yes"]  # existing ids untouched, new appended
    assert len(saved["colors"]) == 4 and saved["colors"][:2] == [[1, 2, 3], [4, 5, 6]]
    assert result["added"] == ["stop", "yes"]


def test_updates_frontend_and_reports_missing_translations(files):
    cfg, js = files
    result = add_signs(["stop", "yes"], cfg, js)
    assert result["frontend_updated"]
    assert 'export const ACTIVE_SIGNS = ["hello", "iloveyou", "stop", "yes"];' in js.read_text()
    assert result["missing_translations"] == ["yes"]  # "stop" already has phrases


def test_duplicates_are_ignored_and_files_untouched(files):
    cfg, js = files
    before = cfg.read_text(), js.read_text()
    assert add_signs(["hello", "Hello"], cfg, js)["added"] == []
    assert (cfg.read_text(), js.read_text()) == before


def test_works_without_the_frontend_file(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(CONFIG))
    result = add_signs(["stop"], cfg, tmp_path / "missing.js")
    assert result["added"] == ["stop"] and not result["frontend_updated"]
