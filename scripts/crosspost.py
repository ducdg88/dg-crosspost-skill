#!/usr/bin/env python3
"""Day bai da len Page sang cac nen tang khac (Zalo, TikTok, YouTube, nhom Zalo...), co luat gio dang.
Cross-post a Page post to other platforms with a posting-hours rule.

Mac dinh CHAY KHO (dry-run): khong gui gi ra ngoai. Them --thuc-su moi gui that.
Chi ghi 'da_dang' khi nen tang tra ve link bai that. Khong in khoa, khong ghi khoa vao file.

Lenh / Commands:
  enqueue-file post.json                 them 1 bai (text, permalink, media) vao hang doi
  enqueue-state state.json [--page ID]   lay bai public co proof HTTP 200 tu state.json cua Fanpage Autopilot
  run [--thuc-su]                        gui cac muc den gio (chay kho neu thieu --thuc-su)
  status                                 xem tinh hinh hang doi
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gio_dang  # noqa: E402

ROOT = os.environ.get("CROSSPOST_HOME", os.getcwd())
QDIR = os.path.join(ROOT, "queue")
LEDGER = os.path.join(QDIR, "ledger.jsonl")
LIMITS = {"tiktok": 2200, "youtube": 4900, "zalo": 2000, "zalo_group": 2000}
SECRET_RE = re.compile(r"(?i)(bearer\s+[a-z0-9._\-]{12,}|access[_-]?token=[^&\s]+|[a-z0-9_\-]{32,})")


def redact(s):
    return SECRET_RE.sub("[da-che]", str(s))


def load_cfg(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clean_caption(text, platform, cfg):
    if cfg.get("bo_gach_dai", True):
        text = re.sub(r"\s*[–—]\s*", ", ", text)
    lim = LIMITS.get(platform, 2000)
    return text if len(text) <= lim else text[: lim - 3].rstrip() + "..."


def ledger_read():
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def ledger_add(ev):
    os.makedirs(QDIR, exist_ok=True)
    ev["ts"] = datetime.now().isoformat(timespec="seconds")
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def items_state():
    """Gop su kien theo (key, nen_tang), su kien sau de len su kien truoc."""
    st = {}
    for e in ledger_read():
        k = (e["key"], e["nen_tang"])
        st[k] = {**st.get(k, {}), **e}
    return st


def post_key(post):
    base = post.get("id") or post.get("permalink") or post.get("text", "")
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def enqueue(post, cfg):
    key = post_key(post)
    st = items_state()
    plats = [p for p, v in cfg["nen_tang"].items() if v.get("bat") and (key, p) not in st]  # chong dang trung
    if not plats:
        print(f"[bo qua] {key}: da co trong hang doi cho moi nen tang dang bat")
        return 0
    for row in gio_dang.plan(gio_dang.now_vn(cfg.get("gio_dang")), plats, cfg.get("gio_dang")):
        ledger_add({"key": key, "nen_tang": row["nen_tang"], "trang_thai": "cho", "luc": row["luc"],
                    "ly_do": row["ly_do"], "post": {k: post.get(k, "") for k in ("text", "permalink", "media")}})
        print(f"[xep lich] {key} -> {row['nen_tang']} luc {row['luc']} ({row['ly_do']})")
    return len(plats)


def send_webhook(url_env, payload):
    url = os.environ.get(url_env, "")
    if not url:
        raise RuntimeError(f"thieu bien moi truong {url_env}")
    if not (url.startswith("https://") or url.startswith("http://127.0.0.1") or url.startswith("http://localhost")):
        raise RuntimeError("webhook phai la https hoac loopback")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


def send_outbox(outdir, platform, payload):
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, f"{platform}-{payload['key']}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"cho_cong_cu_khac": True, "file": p}


def run(cfg, thuc_su):
    now = gio_dang.now_vn(cfg.get("gio_dang"))
    n = 0
    due = sorted(items_state().items(), key=lambda kv: kv[1].get("luc", ""))
    for (key, plat), it in due:
        if it.get("trang_thai") not in ("cho", "hen_lai"):
            continue
        if datetime.fromisoformat(it["luc"]) > now:
            continue
        action, at, why = gio_dang.decide(now, cfg.get("gio_dang"))  # kiem lai gio LUC GUI, khong tin gio da xep
        if action == "hen_lai":
            ledger_add({"key": key, "nen_tang": plat, "trang_thai": "hen_lai",
                        "luc": at.isoformat(timespec="seconds"), "ly_do": why})
            print(f"[hen lai] {plat} {key} -> {at.isoformat(timespec='minutes')} ({why})")
            continue
        pc = cfg["nen_tang"][plat]
        post = it["post"]
        payload = {"key": key, "nen_tang": plat, "text": clean_caption(post.get("text", ""), plat, cfg),
                   "link_goc": post.get("permalink", ""), "media": post.get("media", "")}
        if not thuc_su:
            print(f"[kho] se gui {plat} {key}: {len(payload['text'])} ky tu, kieu '{pc.get('kieu')}'")
            continue
        try:
            if pc.get("kieu") == "webhook":
                res = send_webhook(pc["url_env"], payload)
            elif pc.get("kieu") == "outbox":
                res = send_outbox(pc.get("thu_muc", os.path.join(ROOT, "outbox")), plat, payload)
            else:
                raise RuntimeError("chua cau hinh kieu gui (webhook hoac outbox)")
            link = res.get("permalink", "")
            if link.startswith("http"):
                ledger_add({"key": key, "nen_tang": plat, "trang_thai": "da_dang", "proof": link})
                print(f"[da dang] {plat} {key}")
            else:  # chua co link bai that thi KHONG bao da dang
                ledger_add({"key": key, "nen_tang": plat, "trang_thai": "cho_proof", "ghi_chu": "chua co permalink"})
                print(f"[cho proof] {plat} {key}: nen tang chua tra link bai")
        except Exception as e:  # noqa: BLE001
            ledger_add({"key": key, "nen_tang": plat, "trang_thai": "loi", "loi": redact(e)})
            print(f"[loi] {plat} {key}: {redact(e)}")
        n += 1
    return n


def from_state(path, page, toi_da=30):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    pages = d["pages"] if not page else {page: d["pages"][page]}
    posts = []
    for pid, pg in pages.items():
        for x in pg.get("posted", []):
            if x.get("status") == "public" and str(x.get("proof_http_status")) == "200" and x.get("permalink"):
                posts.append({"id": f"{pid}:{x.get('id')}", "text": x.get("caption") or x.get("title", ""),
                              "permalink": x["permalink"], "media": x.get("name", "")})
    return posts[-toi_da:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=os.path.join(ROOT, "config.json"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("enqueue-file")
    s.add_argument("file")
    s = sub.add_parser("enqueue-state")
    s.add_argument("file")
    s.add_argument("--page")
    s = sub.add_parser("run")
    s.add_argument("--thuc-su", action="store_true")
    sub.add_parser("status")
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    if a.cmd == "enqueue-file":
        with open(a.file, encoding="utf-8") as f:
            enqueue(json.load(f), cfg)
    elif a.cmd == "enqueue-state":
        for p in from_state(a.file, a.page):
            enqueue(p, cfg)
    elif a.cmd == "run":
        run(cfg, a.thuc_su)
    else:
        print(dict(Counter(v.get("trang_thai") for v in items_state().values())) or "hang doi rong")


if __name__ == "__main__":
    main()
