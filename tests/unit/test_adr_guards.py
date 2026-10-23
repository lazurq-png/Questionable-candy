"""The docs-sync guard and stamp in scripts/adr_guards.py.

docs/overview.html is a hand-written summary of the records in docs/; the guard
fails when a record changes, or a new ADR appears, without the page being
brought up to date and re-stamped. Stamping also embeds each record in the
page, so it can show them formatted.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "adr_guards.py"
spec = importlib.util.spec_from_file_location("adr_guards", SCRIPT)
adr_guards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adr_guards)


@pytest.fixture(name="docs")
def fixture_docs(tmp_path):
    """A minimal docs/ tree: the template, one ADR, requirements and data model."""
    (tmp_path / "adr").mkdir()
    (tmp_path / "adr" / "0000-adr-template.md").write_text("template\n")
    (tmp_path / "adr" / "0001-frontend.md").write_text("decision one\n")
    (tmp_path / "requirements.md").write_text("requirements\n")
    (tmp_path / "data-model.md").write_text("model\n")
    (tmp_path / "overview.html").write_text(
        "<body>\n<!-- records:start -->\n<!-- records:end -->\n</body>\n"
    )
    return tmp_path


def stamp(docs):
    sources = docs / "overview.sources"
    adr_guards.stamp_docs(docs, sources, docs / "overview.html")
    return sources


def embedded(docs):
    """The records as the page's script would parse them."""
    html = (docs / "overview.html").read_text(encoding="utf-8")
    data = re.search(r'<script type="application/json" id="records">(.*?)</script>', html, re.S)
    return json.loads(data.group(1))


def test_a_freshly_stamped_tree_is_in_sync(docs):
    sources = stamp(docs)

    assert adr_guards.check_docs_sync(docs, sources) == []


def test_the_template_is_not_a_record(docs):
    assert "adr/0000-adr-template.md" not in adr_guards.canonical_docs(docs)


def test_an_edited_record_fails_and_names_the_file(docs):
    sources = stamp(docs)
    (docs / "adr" / "0001-frontend.md").write_text("decision one, amended\n")

    failures = adr_guards.check_docs_sync(docs, sources)

    assert len(failures) == 1
    assert "adr/0001-frontend.md" in failures[0]
    assert "--stamp" in failures[0]


def test_a_new_adr_fails_until_stamped(docs):
    sources = stamp(docs)
    (docs / "adr" / "0002-middleware.md").write_text("decision two\n")

    assert "adr/0002-middleware.md" in adr_guards.check_docs_sync(docs, sources)[0]
    stamp(docs)
    assert adr_guards.check_docs_sync(docs, sources) == []


def test_line_endings_do_not_count_as_a_change(docs):
    """A CRLF Windows checkout and CI's LF checkout must agree."""
    sources = stamp(docs)
    (docs / "requirements.md").write_bytes(b"requirements\r\n")

    assert adr_guards.check_docs_sync(docs, sources) == []


def test_a_missing_manifest_fails(docs):
    failures = adr_guards.check_docs_sync(docs, docs / "overview.sources")

    assert "missing" in failures[0]


def test_stamping_embeds_every_record_in_the_page(docs):
    stamp(docs)

    assert embedded(docs) == {
        "adr/0001-frontend.md": "decision one\n",
        "requirements.md": "requirements\n",
        "data-model.md": "model\n",
    }


def test_a_record_cannot_close_the_embedding_script(docs):
    (docs / "adr" / "0001-frontend.md").write_text("see </script><b>x</b>\n")
    stamp(docs)

    html = (docs / "overview.html").read_text(encoding="utf-8")
    assert html.count("</script>") == 1
    assert embedded(docs)["adr/0001-frontend.md"] == "see </script><b>x</b>\n"


def test_restamping_replaces_rather_than_appends(docs):
    stamp(docs)
    stamp(docs)

    assert (docs / "overview.html").read_text(encoding="utf-8").count("records:start") == 1


def test_a_page_without_markers_is_not_stamped(docs):
    (docs / "overview.html").write_text("<body></body>\n")
    sources = docs / "overview.sources"

    assert adr_guards.stamp_docs(docs, sources, docs / "overview.html") == 1
    assert not sources.exists()
