import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import gio_dang as g  # noqa: E402

TZ = timezone(timedelta(hours=7))


def t(h, m=0, s=0, d=1):
    return datetime(2026, 10, d, h, m, s, tzinfo=TZ)


class Gio(unittest.TestCase):
    def test_trong_khung_gui_ngay(self):
        for x in (t(7), t(12), t(21, 55), t(22, 0), t(22, 0, 30)):
            self.assertEqual(g.decide(x)[0], "gui_ngay", x)

    def test_qua_22h_hen_sang_mai(self):
        a, at, _ = g.decide(t(22, 1))
        self.assertEqual((a, at), ("hen_lai", t(7, 30, d=2)))
        self.assertEqual(g.decide(t(23, 59))[1], t(7, 30, d=2))

    def test_truoc_7h_hen_sang_nay(self):
        a, at, _ = g.decide(t(3))
        self.assertEqual((a, at), ("hen_lai", t(7, 30)))
        self.assertEqual(g.decide(t(6, 59, 59))[1], t(7, 30))

    def test_gian_cach(self):
        p = g.plan(t(10), ["a", "b", "c"])
        self.assertEqual([r["luc"][11:16] for r in p], ["10:00", "10:10", "10:20"])

    def test_tran_khung_sang_mai(self):
        p = g.plan(t(21, 55), ["a", "b", "c"])
        self.assertEqual(p[0]["hanh_dong"], "gui_ngay")
        self.assertEqual(p[1]["luc"], t(7, 30, d=2).isoformat(timespec="seconds"))
        self.assertEqual(p[2]["luc"], t(7, 40, d=2).isoformat(timespec="seconds"))

    def test_sau_22h_ca_ba_sang_mai(self):
        p = g.plan(t(23), ["a", "b"])
        self.assertTrue(all(r["hanh_dong"] == "hen_lai" and r["luc"].startswith("2026-10-02T07") for r in p))


if __name__ == "__main__":
    unittest.main()
