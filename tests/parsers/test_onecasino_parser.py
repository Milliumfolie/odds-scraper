from sportsbetting.bookmakers.onecasino import parse_onecasino_html
from bs4 import BeautifulSoup

SAMPLE_HTML = """
<div class="date-item">
  <div class="date-title-label text-truncate">10 juni 2025</div>
  <div class="event-container" id="m1">
    <div class="event-team-home">Team A</div>
    <div class="event-team-away">Team B</div>
    <div class="start-time">20:00</div>
    <div class="market-odd_holder"><span class="market-odd_odd">2,0</span></div>
    <div class="market-odd_holder"><span class="market-odd_odd">3,5</span></div>
    <div class="market-odd_holder"><span class="market-odd_odd">3,0</span></div>
  </div>
</div>
"""


def test_parse_onecasino_html_basic():
    soup = BeautifulSoup(SAMPLE_HTML, "lxml")
    parsed = parse_onecasino_html(soup)
    assert "Team A - Team B" in parsed
    match = parsed["Team A - Team B"]
    assert match["odds"]["onecasino"] == [2.0, 3.5, 3.0]
    assert match["id"]["onecasino"] == "m1"
    assert match["competition"]
    assert match["date"] is not None
