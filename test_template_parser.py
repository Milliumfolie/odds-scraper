from sportsbetting.bookmakers.template_parser import parse_template
import dateutil.parser

def test_parse_template_returns_expected_structure():
    res = parse_template()
    assert isinstance(res, dict)
    assert res, "Parser should return at least one match"
    match, data = next(iter(res.items()))
    assert "odds" in data and "id" in data and "date" in data and "competition" in data
    assert isinstance(data["odds"], dict)
    # Check date is parseable
    dateutil.parser.parse(data["date"])