# SPDX-License-Identifier: GPL-3.0-or-later
"""ops.py — 큐 오퍼레이터. 편집·이름 바꾸기·이동·삭제는 큐 버튼 오른쪽 클릭 메뉴에서."""
import traceback

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ImportHelper

from . import store, icons

TEMPLATE = "import bpy\n\n# Cueboard — this script runs when the cue button is clicked.\n"
EDIT_PREFIX = "Cue · "                 # 편집용 텍스트 이름: "Cue · 큐이름.py" (하나를 재사용)


def _is_cueboard_text(t):
    """Cueboard가 만든 편집용 텍스트(지금 것·예전 버전 것)인지."""
    return (t.get("cueboard_edit") is not None or t.get("cueboard") is not None
            or t.name.startswith(("Cueboard Edit", "cue: ", EDIT_PREFIX)))


def edit_target(t):
    """편집 텍스트가 가리키는 (탭 이름, 큐 이름) — 아니면 None."""
    link = t.get("cueboard") if t is not None else None
    if link is None or isinstance(link, str):            # 예전 버전(큐 이름만)
        return None
    return tuple(link)


def is_dirty(t):
    """편집 텍스트가 저장된 큐 내용과 다른지(헤더의 * 표시)."""
    tg = edit_target(t)
    c = store.find_cue(*tg) if tg else None
    return c is not None and t.as_string().rstrip("\n") != c["source"].rstrip("\n")


def _rename_links(old_tab, new_tab, old_cue=None, new_cue=None):
    """열려 있는 편집 텍스트의 연결·이름을 탭·큐 이름 변경에 맞춘다."""
    for t in bpy.data.texts:
        tg = edit_target(t)
        if not tg or tg[0] != old_tab or (old_cue is not None and tg[1] != old_cue):
            continue
        cue = new_cue if old_cue is not None else tg[1]
        t["cueboard"] = [new_tab, cue]
        t.name = f"{EDIT_PREFIX}{cue}.py"[:63]


def user_texts():
    return [t for t in bpy.data.texts if not _is_cueboard_text(t)]


def _redraw(context):
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.type in ('VIEW_3D', 'TEXT_EDITOR'):
                area.tag_redraw()


def _text_editor_text(context):
    sp = getattr(context, "space_data", None)
    if sp is not None and sp.type == 'TEXT_EDITOR' and sp.text is not None:
        return sp.text
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'TEXT_EDITOR' and area.spaces.active.text is not None:
                return area.spaces.active.text
    return None


def _show_in_text_editor(context, text):
    """열린 Text Editor가 있으면 거기, 없으면 새 창을 띄워 text를 보여 준다. 보여 줬는지 여부."""
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'TEXT_EDITOR':
                area.spaces.active.text = text
                area.spaces.active.top = 0
                area.tag_redraw()
                return True
    # 지금 창의 영역 하나를 새 창으로 복제한 뒤 Text Editor로 바꾼다(원래 영역은 그대로)
    win = context.window
    area = context.area or (win.screen.areas[0] if win and win.screen.areas else None)
    if win is None or area is None:
        return False
    before = set(context.window_manager.windows[:])
    try:
        with context.temp_override(window=win, area=area):
            bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
    except RuntimeError:
        return False
    new = [w for w in context.window_manager.windows if w not in before]
    if not new:
        return False
    a = new[0].screen.areas[0]
    a.type = 'TEXT_EDITOR'
    sp = a.spaces.active
    sp.text = text
    sp.top = 0
    sp.show_line_numbers = True
    sp.show_syntax_highlight = True
    return True


# ── 탭 ───────────────────────────────────────────────────
class CUEBOARD_OT_tab_select(bpy.types.Operator):
    bl_idname = "cueboard.tab_select"
    bl_label = "Select Tab"
    bl_description = "Show this tab (right-click to rename)"

    index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        store.set_active(self.index)
        store.save()
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_tab_add(bpy.types.Operator):
    bl_idname = "cueboard.tab_add"
    bl_label = "New Tab"
    bl_description = "Add a tab (right-click it to rename)"

    def execute(self, context):
        name = store.unique("Tab", {t["name"] for t in store.tabs()})
        store.tabs().append({"name": name, "cues": []})
        store.set_active(len(store.tabs()) - 1)
        store.save()
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_tab_rename(bpy.types.Operator):
    bl_idname = "cueboard.tab_rename"
    bl_label = "Rename Tab"
    bl_description = "Rename this tab"

    index: IntProperty(options={'HIDDEN'})
    name: StringProperty(name="Name")

    def invoke(self, context, event):
        if not (0 <= self.index < len(store.tabs())):
            return {'CANCELLED'}
        self.name = store.tabs()[self.index]["name"]
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not (0 <= self.index < len(store.tabs())) or not self.name.strip():
            return {'CANCELLED'}
        tab = store.tabs()[self.index]
        old = tab["name"]
        tab["name"] = store.unique(self.name, {t["name"] for t in store.tabs() if t is not tab})
        _rename_links(old, tab["name"])
        store.save()
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_tab_move(bpy.types.Operator):
    bl_idname = "cueboard.tab_move"
    bl_label = "Move Tab"
    bl_description = "Move this tab left or right"

    index: IntProperty(options={'HIDDEN'})
    direction: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ts = store.tabs()
        i, j = self.index, self.index + self.direction
        if not (0 <= i < len(ts) and 0 <= j < len(ts)):
            return {'CANCELLED'}
        current = store.active_tab()
        ts[i], ts[j] = ts[j], ts[i]
        store.set_active(ts.index(current))               # 보고 있던 탭은 그대로 선택
        store.save()
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_tab_delete(bpy.types.Operator):
    bl_idname = "cueboard.tab_delete"
    bl_label = "Delete Tab"
    bl_description = "Delete this tab and all its cues"

    index: IntProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return len(store.tabs()) > 1                      # 마지막 탭은 지우지 않음

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        ts = store.tabs()
        if not (0 <= self.index < len(ts)) or len(ts) <= 1:
            return {'CANCELLED'}
        current = store.active_tab()
        removed = ts.pop(self.index)
        store.set_active(ts.index(current) if current is not removed else min(self.index, len(ts) - 1))
        store.save()
        _redraw(context)
        return {'FINISHED'}


# ── 등록 ─────────────────────────────────────────────────
_text_items = []


def _texts(self, context):
    _text_items.clear()
    _text_items.extend((t.name, t.name, "") for t in user_texts())
    return _text_items or [("", "(no texts)", "")]


class CUEBOARD_OT_cue_add_text(bpy.types.Operator):
    bl_idname = "cueboard.cue_add_text"
    bl_label = "Add Cue from Text"
    bl_description = "Register a Text Editor script as a cue"

    name: StringProperty(name="Name")
    text: EnumProperty(name="Text", items=_texts)

    @classmethod
    def poll(cls, context):
        return len(user_texts()) > 0

    def invoke(self, context, event):
        t = _text_editor_text(context)
        if t is None or _is_cueboard_text(t):
            t = user_texts()[0]
        self.text = t.name
        self.name = t.name[:-3] if t.name.endswith(".py") else t.name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        t = bpy.data.texts.get(self.text)
        if t is None:
            return {'CANCELLED'}
        name = store.unique(self.name, {c["name"] for c in store.cues()})
        store.cues().append({"name": name, "source": t.as_string()})
        store.save()
        self.report({'INFO'}, f"Cue added: {name}")
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_cue_new(bpy.types.Operator):
    """Maya 셸프처럼 빈 버튼만 바로 추가(이름·내용은 나중에 오른쪽 클릭으로)."""
    bl_idname = "cueboard.cue_new"
    bl_label = "New Cue"
    bl_description = "Add an empty cue (right-click it to edit or rename)"

    def execute(self, context):
        name = store.unique("Cue", {c["name"] for c in store.cues()})
        store.cues().append({"name": name, "source": TEMPLATE})
        store.save()
        _redraw(context)
        return {'FINISHED'}


# ── 큐 하나를 다루는 것들 ─────────────────────────────────
class _CueOp:
    index: IntProperty(options={'HIDDEN'})

    def cue(self):
        cs = store.cues()
        return cs[self.index] if 0 <= self.index < len(cs) else None


class CUEBOARD_OT_cue_run(_CueOp, bpy.types.Operator):
    bl_idname = "cueboard.cue_run"
    bl_label = "Run Cue"
    bl_description = "Run this cue (right-click for more)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, props):
        # 격자 칸에는 이름이 다 안 보이므로 툴팁에 이름 + 첫 주석
        cs = store.cues()
        if 0 <= props.index < len(cs):
            c = cs[props.index]
            first = next((ln for ln in c["source"].splitlines() if ln.strip().startswith("#")), "")
            text = first.lstrip("# ").strip()
            return f"{c['name']}\n{text}" if text else c["name"]
        return "Run this cue (right-click for more)"

    def execute(self, context):
        c = self.cue()
        if c is None:
            return {'CANCELLED'}
        ns = {"__name__": "__main__", "__file__": f"<cue {c['name']}>"}
        try:
            exec(compile(c["source"], f"<cue {c['name']}>", "exec"), ns)
        except Exception as e:  # noqa: BLE001 — 사용자 스크립트 오류는 알리고 Blender는 계속
            traceback.print_exc()
            self.report({'ERROR'}, f"{c['name']}: {type(e).__name__}: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class CUEBOARD_OT_cue_edit(_CueOp, bpy.types.Operator):
    bl_idname = "cueboard.cue_edit"
    bl_label = "Edit Cue"
    bl_description = "Open this cue in the Text Editor"

    def execute(self, context):
        c = self.cue()
        if c is None:
            return {'CANCELLED'}
        t = next((x for x in bpy.data.texts if x.get("cueboard_edit")), None) \
            or bpy.data.texts.new("Cue.py")
        t["cueboard_edit"] = True
        t.name = f"{EDIT_PREFIX}{c['name']}.py"[:63]          # 이름 칸만 봐도 어떤 큐인지
        t.clear()
        t.write(c["source"])
        t.cursor_set(0)                                      # 쓰고 나면 커서가 끝에 있어 끝으로 스크롤되므로 첫 줄로
        t["cueboard"] = [store.active_tab()["name"], c["name"]]   # 지금 어떤 큐를 편집 중인지
        if not _show_in_text_editor(context, t):
            self.report({'INFO'}, f"Open a Text Editor to edit “{t.name}”")
        else:
            self.report({'INFO'}, f"Editing “{c['name']}” — Ctrl+S or Save Cue to save")
        return {'FINISHED'}


class CUEBOARD_OT_cue_update(bpy.types.Operator):
    bl_idname = "cueboard.cue_update"
    bl_label = "Update Cue from Text"
    bl_description = "Save the edited text back into its cue"

    text: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        t = bpy.data.texts.get(self.text)
        tg = edit_target(t)
        c = store.find_cue(*tg) if tg else None
        if c is None:
            self.report({'ERROR'}, "The cue for this text no longer exists")
            return {'CANCELLED'}
        c["source"] = t.as_string()
        store.save()
        self.report({'INFO'}, f"Cue updated: {c['name']}")
        return {'FINISHED'}


class CUEBOARD_OT_cue_save(bpy.types.Operator):
    """편집 창에서 쓰는 저장(헤더 버튼·Ctrl+S). 큐 편집용 텍스트가 아닐 때는 poll이 꺼져
    Ctrl+S가 원래 기능(.blend 저장)으로 넘어간다."""
    bl_idname = "cueboard.cue_save"
    bl_label = "Save Cue"
    bl_description = "Save this text into its cue"

    @classmethod
    def poll(cls, context):
        sp = getattr(context, "space_data", None)
        t = sp.text if sp is not None and sp.type == 'TEXT_EDITOR' else None
        return edit_target(t) is not None

    def execute(self, context):
        return bpy.ops.cueboard.cue_update(text=context.space_data.text.name)


class CUEBOARD_OT_cue_rename(_CueOp, bpy.types.Operator):
    bl_idname = "cueboard.cue_rename"
    bl_label = "Rename Cue"
    bl_description = "Rename this cue"

    name: StringProperty(name="Name")

    def invoke(self, context, event):
        c = self.cue()
        if c is None:
            return {'CANCELLED'}
        self.name = c["name"]
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        c = self.cue()
        if c is None or not self.name.strip():
            return {'CANCELLED'}
        old = c["name"]
        c["name"] = store.unique(self.name, {x["name"] for x in store.cues() if x is not c})
        tab = store.active_tab()["name"]
        _rename_links(tab, tab, old, c["name"])          # 열려 있는 편집 텍스트도 새 이름으로
        store.save()
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_cue_move(_CueOp, bpy.types.Operator):
    bl_idname = "cueboard.cue_move"
    bl_label = "Move Cue"
    bl_description = "Move this cue up or down"

    direction: IntProperty(default=-1)

    def execute(self, context):
        cs = store.cues()
        j = self.index + self.direction
        if self.cue() is None or not (0 <= j < len(cs)):
            return {'CANCELLED'}
        cs[self.index], cs[j] = cs[j], cs[self.index]
        store.save()
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_cue_delete(_CueOp, bpy.types.Operator):
    bl_idname = "cueboard.cue_delete"
    bl_label = "Delete Cue"
    bl_description = "Delete this cue"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        c = self.cue()
        if c is None:
            return {'CANCELLED'}
        store.cues().remove(c)
        store.save()
        _redraw(context)
        return {'FINISHED'}


_icon_items = []


def _icon_enum(self, context):
    if not _icon_items:
        _icon_items.extend((n, n, "", n, i) for i, n in enumerate(icons.builtin_icons()))
    return _icon_items


class CUEBOARD_OT_cue_icon(_CueOp, bpy.types.Operator):
    """Blender 내장 아이콘을 검색해서 고른다(목록에 아이콘 그림이 같이 보임)."""
    bl_idname = "cueboard.cue_icon"
    bl_label = "Set Icon"
    bl_description = "Choose a Blender icon for this cue"
    bl_property = "icon"

    icon: EnumProperty(items=_icon_enum)

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        c = self.cue()
        if c is None:
            return {'CANCELLED'}
        c["icon"] = self.icon
        c.pop("image", None)
        store.save()
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_cue_image(_CueOp, bpy.types.Operator, ImportHelper):
    bl_idname = "cueboard.cue_image"
    bl_label = "Set Image Icon"
    bl_description = "Use an image file (PNG, JPG) as this cue's icon"

    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg;*.bmp;*.tga", options={'HIDDEN'})

    def execute(self, context):
        c = self.cue()
        if c is None or not icons.can_load(self.filepath):
            self.report({'ERROR'}, "Could not load the image")
            return {'CANCELLED'}
        c["image"] = self.filepath
        c.pop("icon", None)
        store.save()
        _redraw(context)
        return {'FINISHED'}


class CUEBOARD_OT_cue_icon_clear(_CueOp, bpy.types.Operator):
    bl_idname = "cueboard.cue_icon_clear"
    bl_label = "Clear Icon"
    bl_description = "Show this cue's name instead of an icon"

    def execute(self, context):
        c = self.cue()
        if c is None:
            return {'CANCELLED'}
        c.pop("icon", None)
        c.pop("image", None)
        store.save()
        _redraw(context)
        return {'FINISHED'}


classes = (CUEBOARD_OT_tab_select, CUEBOARD_OT_tab_add, CUEBOARD_OT_tab_rename, CUEBOARD_OT_tab_move,
           CUEBOARD_OT_tab_delete, CUEBOARD_OT_cue_icon, CUEBOARD_OT_cue_image, CUEBOARD_OT_cue_icon_clear,CUEBOARD_OT_cue_add_text, CUEBOARD_OT_cue_new, CUEBOARD_OT_cue_run, CUEBOARD_OT_cue_edit,
           CUEBOARD_OT_cue_update, CUEBOARD_OT_cue_save, CUEBOARD_OT_cue_rename, CUEBOARD_OT_cue_move, CUEBOARD_OT_cue_delete)
