# SPDX-License-Identifier: GPL-3.0-or-later
"""icons.py — 큐 아이콘: Blender 내장 아이콘 이름 또는 이미지 파일(PNG 등)."""
import os

import bpy
import bpy.utils.previews

_pcoll = None


def _coll():
    global _pcoll
    if _pcoll is None:
        _pcoll = bpy.utils.previews.new()
    return _pcoll


def _preview(path):
    if not path or not os.path.isfile(path):
        return None
    pc = _coll()
    if path not in pc:
        try:
            pc.load(path, path, 'IMAGE')
        except (KeyError, RuntimeError):
            return None
    return pc[path]


def can_load(path):
    """이미지로 읽히는지(크기가 있는지). UI 없이 돌릴 때도 확인 가능."""
    p = _preview(path)
    return p is not None and p.image_size[0] > 0


def image_icon_id(path):
    """이미지 파일의 아이콘 id — 없거나 못 읽으면 0(그때는 이름 글자로 표시)."""
    p = _preview(path)
    return p.icon_id if p is not None else 0


def builtin_icons():
    return [i.identifier for i in bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items
            if i.identifier != 'NONE']


def free():
    global _pcoll
    if _pcoll is not None:
        bpy.utils.previews.remove(_pcoll)
        _pcoll = None
