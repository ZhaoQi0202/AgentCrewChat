from __future__ import annotations

import re

_MODIFY_HINT = re.compile(
    r"改成|改为|修改|调整|加上|删掉|删除|换一下|请把|能不能|不要这样",
)
_NEGATIVE = re.compile(r"不太好|不行|还没|别\s*(开|动)|暂缓|取消")
_POSITIVE_TOKEN = (
    "好的",
    "好滴",
    "好哒",
    "没问题",
    "可以",
    "确认",
    "同意",
    "开始吧",
    "开始",
    "ok",
    "yes",
    "行",
    "嗯好",
    "好啊",
    "就这么办",
    "就这样",
    "就这样吧",
    "开工",
    "上吧",
    "确认了",
    "是的",
    "嗯",
)


def is_user_confirmation(text: str) -> bool:
    t = (text or "").strip()
    if not t or len(t) > 120:
        return False
    if _NEGATIVE.search(t):
        return False
    if _MODIFY_HINT.search(t):
        return False
    tl = t.lower()
    for p in _POSITIVE_TOKEN:
        if p.isascii():
            if p in tl:
                return True
        elif p in t:
            return True
    if re.match(r"^[好嗯行可以的确认同意没问题okyes\s，。！是的OK]+$", t, re.IGNORECASE):
        return True
    return False
