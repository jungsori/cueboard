# SPDX-License-Identifier: GPL-3.0-or-later
"""
store.py — 탭·큐 저장소(JSON, 사용자 폴더). 모든 .blend 파일이 같은 탭을 본다.

형식(버전 3): {"version": 3, "active": 0, "tabs": [{"name": "Main", "cues": [{"name", "source", ...}]}]}
  버전 2(큐 목록 하나) → "Main" 탭 하나로, 버전 1(보드 여러 개) → 보드마다 탭으로.
"""
import json
import os

import bpy

FILE_NAME = "boards.json"
_cache = None


def _folder():
    try:
        return bpy.utils.extension_path_user(__package__, create=True)
    except Exception:  # noqa: BLE001 — 예전 방식 애드온으로 설치된 경우
        return bpy.utils.user_resource('CONFIG', path="cueboard", create=True)


def path():
    return os.path.join(_folder(), FILE_NAME)


def _migrate(d):
    if isinstance(d.get("tabs"), list):
        tabs = d["tabs"]
    elif isinstance(d.get("cues"), list):                     # 버전 2
        tabs = [{"name": "Main", "cues": d["cues"]}]
    else:                                                     # 버전 1
        tabs = [{"name": b.get("name", "Tab"), "cues": b.get("cues", [])} for b in d.get("boards", [])]
    if not tabs:
        tabs = [{"name": "Main", "cues": []}]
    act = d.get("active", 0)
    return {"version": 3, "active": act if isinstance(act, int) and 0 <= act < len(tabs) else 0, "tabs": tabs}


def data():
    global _cache
    if _cache is None:
        try:
            with open(path(), encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict):
                raise ValueError
        except (OSError, ValueError):
            d = {}
        _cache = _migrate(d)
    return _cache


def tabs():
    return data()["tabs"]


def active_index():
    return data()["active"]


def set_active(i):
    if 0 <= i < len(tabs()):
        data()["active"] = i


def active_tab():
    return tabs()[active_index()]


def cues():
    """지금 탭의 큐."""
    return active_tab()["cues"]


def find_cue(tab_name, cue_name):
    t = next((t for t in tabs() if t["name"] == tab_name), None)
    return next((c for c in t["cues"] if c["name"] == cue_name), None) if t else None


def save():
    tmp = path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data(), f, ensure_ascii=False, indent=1)
    os.replace(tmp, path())                                   # 쓰다가 끊겨도 기존 파일이 안 깨지게


def reload():
    global _cache
    _cache = None
    return data()


def unique(name, taken):
    name = (name or "").strip() or "Cue"
    if name not in taken:
        return name
    i = 1
    while f"{name}.{i:03d}" in taken:
        i += 1
    return f"{name}.{i:03d}"
