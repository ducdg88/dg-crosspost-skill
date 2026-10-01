#!/usr/bin/env python3
"""Kiem tra ket noi va tu kiem, KHONG gui bai that, KHONG in khoa.
Check connections and self-test. Never posts, never prints secrets.

  python kiem_ket_noi.py --config config.json           xem moi nen tang da cau hinh chua (chi in TEN bien, co/thieu)
  python kiem_ket_noi.py --config config.json --ping    them thu mo ket noi TCP toi may chu webhook (khong gui du lieu)
  python kiem_ket_noi.py --tu-kiem                      chay thu tron mach o thu muc tam: xep lich, chay kho, soat ro ri
"""
import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SECRET_PATTERNS = [r"AIza[0-9A-Za-z_\-]{30,}", r"sk-[A-Za-z0-9]{20,}", r"gh[pousr]_[A-Za-z0-9]{30,}",
                   r"xox[baprs]-[A-Za-z0-9\-]{10,}", r"(?i)bearer\s+[a-z0-9._\-]{20,}",
                   r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[a-z]{2,}"]


def check_config(path, ping):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    ok_all = True
    for name, pc in cfg.get("nen_tang", {}).items():
        if not pc.get("bat"):
            print(f"[tat]   {name}")
            continue
        kieu = pc.get("kieu")
        if kieu == "webhook":
            env = pc.get("url_env", "")
            url = os.environ.get(env, "")
            if not url:
                print(f"[THIEU] {name}: chua dat bien moi truong {env}")
                ok_all = False
                continue
            u = urlparse(url)
            loopback = u.hostname in ("127.0.0.1", "localhost")
            if u.scheme != "https" and not loopback:
                print(f"[SAI]   {name}: webhook phai https hoac loopback")
                ok_all = False
                continue
            line = f"[OK]    {name}: bien {env} da dat, may chu {u.scheme}://{u.hostname}"
            if ping:
                port = u.port or (443 if u.scheme == "https" else 80)
                try:
                    socket.create_connection((u.hostname, port), timeout=5).close()
                    line += ", mo duoc ket noi TCP"
                except OSError as e:
                    line = f"[LOI]   {name}: khong mo duoc ket noi toi {u.hostname}:{port} ({type(e).__name__})"
                    ok_all = False
            print(line)
        elif kieu == "outbox":
            print(f"[OK]    {name}: ghi file vao thu muc '{pc.get('thu_muc', 'outbox')}' cho cong cu khac lay")
        else:
            print(f"[SAI]   {name}: chua khai kieu gui (webhook hoac outbox)")
            ok_all = False
    return ok_all


def leak_scan():
    bad = []
    for base, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "queue", "outbox")]
        for fn in files:
            if fn in ("kiem_ket_noi.py", "crosspost.py") or fn.endswith((".pyc", ".png", ".jpg")):
                continue
            try:
                txt = open(os.path.join(base, fn), encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            for pat in SECRET_PATTERNS:
                if re.search(pat, txt):
                    bad.append(os.path.relpath(os.path.join(base, fn), REPO))
                    break
    return bad


def tu_kiem():
    ok = True
    gi = open(os.path.join(REPO, ".gitignore"), encoding="utf-8").read()
    for need in ("config.json", ".env", "queue/", "outbox/"):
        good = need in gi
        ok &= good
        print(f"[{'OK' if good else 'LOI'}]    .gitignore co '{need}'")
    leaks = leak_scan()
    print(f"[{'OK' if not leaks else 'LOI'}]    quet ro ri khoa/email trong repo: {leaks or 'sach'}")
    ok &= not leaks
    with tempfile.TemporaryDirectory() as tmp:
        cfg = os.path.join(tmp, "config.json")
        with open(os.path.join(REPO, "config.example.json"), encoding="utf-8") as f:
            data = json.load(f)
        data["nen_tang"]["zalo_group"]["thu_muc"] = os.path.join(tmp, "outbox")
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump(data, f)
        post = os.path.join(tmp, "post.json")
        with open(post, "w", encoding="utf-8") as f:
            json.dump({"id": "tu-kiem-1", "text": "Bai thu — khong dang that", "permalink": "https://example.invalid/p/1"}, f)
        env = {**os.environ, "CROSSPOST_HOME": tmp}
        for args in (["enqueue-file", post], ["run"], ["status"]):
            r = subprocess.run([sys.executable, os.path.join(HERE, "crosspost.py"), "--config", cfg] + args,
                               env=env, capture_output=True, text=True, encoding="utf-8")
            good = r.returncode == 0
            ok &= good
            print(f"[{'OK' if good else 'LOI'}]    crosspost {args[0]}: " + (r.stdout.strip().splitlines() or [''])[-1][:110])
        sent = os.path.exists(os.path.join(tmp, "outbox"))
        print(f"[{'OK' if not sent else 'LOI'}]    chay kho khong gui gi (khong co file outbox)")
        ok &= not sent
    print("KET QUA:", "DAT" if ok else "KHONG DAT")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config")
    ap.add_argument("--ping", action="store_true")
    ap.add_argument("--tu-kiem", action="store_true")
    a = ap.parse_args()
    good = True
    if a.config:
        good &= check_config(a.config, a.ping)
    if a.tu_kiem or not a.config:
        good &= tu_kiem()
    sys.exit(0 if good else 1)
