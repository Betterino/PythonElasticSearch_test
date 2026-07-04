from scripts.import_csv import parse_rubrics


def test_parse_rubrics_normal_list():
    raw = "['VK-1603736028819866', 'VK-11879320040']"
    assert parse_rubrics(raw) == ["VK-1603736028819866", "VK-11879320040"]


def test_parse_rubrics_empty_string():
    assert parse_rubrics("") == []