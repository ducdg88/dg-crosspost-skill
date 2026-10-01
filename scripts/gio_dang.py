"""Luat gio dang / Posting-hours rule (VN/EN).

Mac dinh: gui duoc trong khung 07:00 den 22:00 (gio Viet Nam, UTC+7). Qua 22:00 thi hen lai
sang hom sau luc 07:30. Cac nen tang gui cach nhau `gian_cach_phut` de khong dang don (chong spam).
Default: send between 07:00 and 22:00 (UTC+7). After 22:00 defer to 07:30 next day. Platforms are staggered.
"""
from datetime import datetime, timedelta, timezone

DEFAULTS = {
    "mui_gio": 7,              # UTC+7, Viet Nam khong co gio mua he
    "gio_bat_dau": "07:00",
    "gio_ket_thuc": "22:00",   # gui duoc den het 22:00:59, qua la hen lai
    "gio_hen_sang": "07:30",
    "gian_cach_phut": 10,
}


def _hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _cfg(cfg):
    c = dict(DEFAULTS)
    c.update(cfg or {})
    return c


def now_vn(cfg=None):
    return datetime.now(timezone(timedelta(hours=_cfg(cfg)["mui_gio"])))


def _at(day, hm, tz):
    h, m = divmod(_hm(hm), 60)
    return datetime(day.year, day.month, day.day, h, m, tzinfo=tz)


def trong_khung(t, cfg=None):
    """True neu thoi diem t nam trong khung duoc phep gui."""
    c = _cfg(cfg)
    start = _at(t, c["gio_bat_dau"], t.tzinfo)
    end = _at(t, c["gio_ket_thuc"], t.tzinfo) + timedelta(seconds=59)
    return start <= t <= end


def decide(t, cfg=None):
    """Tra ve (hanh_dong, thoi_diem, ly_do). hanh_dong: 'gui_ngay' hoac 'hen_lai'."""
    c = _cfg(cfg)
    if trong_khung(t, c):
        return "gui_ngay", t, "trong khung gio"
    start_today = _at(t, c["gio_bat_dau"], t.tzinfo)
    if t < start_today:  # ngay som, truoc gio bat dau: hen sang cung ngay
        return "hen_lai", _at(t, c["gio_hen_sang"], t.tzinfo), "truoc gio bat dau, hen sang nay"
    nxt = t + timedelta(days=1)
    return "hen_lai", _at(nxt, c["gio_hen_sang"], t.tzinfo), "qua gio ket thuc, hen sang mai"


def plan(t, platforms, cfg=None):
    """Xep lich cho tung nen tang, cach nhau gian_cach_phut. Slot nao rot ra ngoai khung thi sang mai 07:30."""
    c = _cfg(cfg)
    gap = timedelta(minutes=int(c["gian_cach_phut"]))
    action, cur, why = decide(t, c)
    out = []
    for i, p in enumerate(platforms):
        if i:
            cur = cur + gap
            if not trong_khung(cur, c):
                _, cur, why = decide(cur, c)
                action = "hen_lai"
        out.append({"nen_tang": p, "luc": cur.isoformat(timespec="seconds"),
                    "hanh_dong": "gui_ngay" if cur == t else "hen_lai", "ly_do": why})
    return out
