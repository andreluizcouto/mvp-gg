from opgg_client import _parse_lane_meta

SHARED_CLASS = """class LolListLaneMetaChampions: data
class Data: positions
class Positions: top,mid,jungle,adc,support
class Top: champion,is_rip,play,win_rate,tier,rank

LolListLaneMetaChampions(Data(Positions([Top("Malphite",false,110012,0.51,1,1),Top("Darius",false,117375,0.51,1,2)],[Top("Ahri",false,155226,0.51,1,1)],[Top("Wukong",true,98504,0.52,1,1)],[Top("Kai'Sa",false,1,0.5,2,1)],[Top("Nunu & Willump",false,2,0.49,3,1)])))
"""

PER_POSITION_CLASS = """class Positions: top,mid
class Top: champion,tier
class Mid: champion,win_rate,tier

LolListLaneMetaChampions(Data(Positions([Top("Garen",1)],[Mid("Syndra",0.5,2)])))
"""


def test_parses_lists_in_positions_order_with_shared_class():
    result = _parse_lane_meta(SHARED_CLASS)
    assert [r["champion"] for r in result["top"]] == ["Malphite", "Darius"]
    assert result["mid"][0]["champion"] == "Ahri"
    assert result["jungle"][0]["is_rip"] is True
    assert result["adc"][0]["champion"] == "Kai'Sa"
    assert result["support"][0] == {
        "champion": "Nunu & Willump", "is_rip": False, "play": 2, "win_rate": 0.49, "tier": 3, "rank": 1,
    }


def test_parses_per_position_classes():
    result = _parse_lane_meta(PER_POSITION_CLASS)
    assert result["top"] == [{"champion": "Garen", "tier": 1}]
    assert result["mid"] == [{"champion": "Syndra", "win_rate": 0.5, "tier": 2}]


def test_returns_empty_without_positions():
    assert _parse_lane_meta("class Top: champion\n") == {}
