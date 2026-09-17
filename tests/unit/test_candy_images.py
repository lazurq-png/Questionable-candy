"""The static candy pictures and the seed data that points at them.

These SVGs are served from the site's own origin. Opened directly rather than
through an <img>, an SVG runs its scripts with the site's cookies in reach, so a
script or an event handler in one of these files would be stored XSS. The scan
below is the guard; it parses the files rather than grepping them, so an
attribute split across lines or oddly cased still counts.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders

from shop.management.commands.seed_candy import CANDIES

CANDY_DIR = Path(__file__).resolve().parents[2] / "shop" / "static" / "shop" / "candy"
SVGS = sorted(CANDY_DIR.glob("*.svg"))
MAX_BYTES = 4096


def local_name(name):
    """'{http://www.w3.org/2000/svg}title' -> 'title'."""
    return name.rsplit("}", 1)[-1]


def test_the_candy_directory_holds_pictures():
    """Otherwise every parametrized test below silently collects nothing."""
    assert len(SVGS) >= len(CANDIES) + 1


# <style> can @import or url() anything; <animate>/<set> can rewrite an href
# after load, past every attribute check below.
FORBIDDEN_ELEMENTS = {"script", "foreignobject", "style", "animate", "set"}
# url( followed by anything but a same-document fragment.
EXTERNAL_URL = re.compile(r"url\(\s*['\"]?(?!#)", re.IGNORECASE)


@pytest.mark.parametrize("svg", SVGS, ids=lambda p: p.name)
def test_svg_cannot_run_code_or_load_anything(svg):
    """No script, handler, styling or animation, and no external reference."""
    root = ET.parse(svg).getroot()
    for element in root.iter():
        tag = local_name(element.tag).lower()
        assert tag not in FORBIDDEN_ELEMENTS, f"{svg.name}: <{tag}>"
        for attribute, value in element.attrib.items():
            name = local_name(attribute).lower()
            assert not name.startswith("on"), f"{svg.name}: event handler {name}"
            if name == "href":
                assert value.startswith("#"), f"{svg.name}: external reference {value}"
            assert not EXTERNAL_URL.search(value), f"{svg.name}: {name}={value}"
    text = svg.read_text(encoding="utf-8").lower()
    assert "<script" not in text
    assert not EXTERNAL_URL.search(text), f"{svg.name}: external url()"


@pytest.mark.parametrize("svg", SVGS, ids=lambda p: p.name)
def test_svg_is_small_titled_and_scalable(svg):
    """A viewBox to scale, role and title for assistive tech, and a size cap."""
    root = ET.parse(svg).getroot()
    assert local_name(root.tag) == "svg"
    assert root.get("viewBox"), f"{svg.name} has no viewBox"
    assert root.get("role") == "img"
    title = next((e for e in root if local_name(e.tag) == "title"), None)
    assert title is not None and title.text and title.text.strip()
    assert svg.stat().st_size <= MAX_BYTES


def test_there_is_a_placeholder_for_candy_without_a_picture():
    """The templates fall back to it when Candy.image is blank."""
    assert finders.find("shop/candy/placeholder.svg")


@pytest.mark.parametrize("candy", CANDIES, ids=lambda c: c["name"])
def test_every_seeded_candy_has_a_picture_that_exists(candy):
    """Resolved through staticfiles, the same way {% static %} finds it."""
    assert candy["image"], f"{candy['name']} has no image"
    assert finders.find(candy["image"]), f"missing static file {candy['image']}"


def test_every_picture_belongs_to_a_seeded_candy_or_is_the_placeholder():
    """A picture nothing points at is a rename that went half-way."""
    referenced = {Path(c["image"]).name for c in CANDIES} | {"placeholder.svg"}
    assert {p.name for p in SVGS} == referenced


def test_seeded_names_are_unique():
    """The seed matches rows by name, and the database does not enforce it."""
    names = [c["name"] for c in CANDIES]
    assert len(names) == len(set(names))


def test_every_seeded_candy_discloses_a_real_flaw():
    """UC-06: a disclosure, never a placeholder."""
    for candy in CANDIES:
        assert candy["flaw"].strip(), candy["name"]
        assert candy["description"].strip(), candy["name"]
