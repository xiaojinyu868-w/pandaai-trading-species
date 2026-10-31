import json

from .paths import DESIGN

_T = json.loads((DESIGN / "tokens.json").read_text(encoding="utf-8"))

C = dict(_T["color"])
SEASON = {k: dict(v) for k, v in _T["season"].items()}
SEASON_ORDER = ["spring", "summer", "autumn", "winter"]
for _k, _v in zip(SEASON_ORDER, ["入场", "狂热", "松动", "危机"]):
    SEASON[_k].setdefault("name", _v)

# 系统警示色（穿仓、熔断、风险提示）：不用红绿，用芥末黄 + 墨色。
WARN = C["mustard"]

# 玩家色：避开纯红纯绿，配形状记号照顾色弱。雾紫不在 tokens 里（需要第五种可区分的颜色）。
PLAYERS = [
    {"id": "p1", "name": "海蓝", "color": C["sky_deep"], "shape": "circle", "mark": "●"},
    {"id": "p2", "name": "芥黄", "color": C["mustard"], "shape": "triangle", "mark": "▲"},
    {"id": "p3", "name": "赭橙", "color": C["ochre"], "shape": "square", "mark": "■"},
    {"id": "p4", "name": "雾紫", "color": "#7B6B9E", "shape": "diamond", "mark": "◆"},
    {"id": "p5", "name": "天青", "color": C["sky_light"], "shape": "star", "mark": "★"},
]
AI_COLOR = C["ink_3"]

# 物种色（物种币、牌角）。如果 decks.json 给了颜色，以内容为准。
SPECIES_COLOR = {
    "cheetah": C["mustard"],
    "elephant": C["ink_3"],
    "fox": C["ochre"],
    "owl": C["sky_deep"],
    "meerkat": C["sky"],
    "chameleon": C["sage"],
    "beaver": C["ink_2"],
}
SPECIES_ORDER = ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon", "beaver"]
SPECIES_CN = {
    "cheetah": "猎豹", "elephant": "大象", "fox": "狐狸", "owl": "猫头鹰",
    "meerkat": "狐獴", "chameleon": "变色龙", "beaver": "海狸",
}
SPECIES_EN = {
    "cheetah": "CHEETAH", "elephant": "ELEPHANT", "fox": "FOX", "owl": "OWL",
    "meerkat": "MEERKAT", "chameleon": "CHAMELEON", "beaver": "BEAVER",
}
# 单字印章，用在黑白委托单和小格子里
SPECIES_SEAL = {
    "cheetah": "豹", "elephant": "象", "fox": "狐", "owl": "鹰",
    "meerkat": "獴", "chameleon": "变", "beaver": "狸",
}

EVIDENCE_KIND = {
    "price": {"cn": "量价", "en": "PRICE & VOLUME", "color": C["sky_deep"], "icon": "chart", "feel": "行情纸带"},
    "data": {"cn": "数据", "en": "DATA LEDGER", "color": C["ochre"], "icon": "ledger", "feel": "账本"},
    "news": {"cn": "消息", "en": "NEWS WIRE", "color": C["ink"], "icon": "phone", "feel": "快讯电报"},
    "tip": {"cn": "锦囊", "en": "OWL'S LETTER", "color": C["mustard"], "icon": "letter", "feel": "猫头鹰的信"},
}
