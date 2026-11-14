# SPDX-License-Identifier: GPL-3.0-or-later
"""ui.py — 사이드바 패널(3D 뷰·Text Editor)과 큐 버튼 오른쪽 클릭 메뉴."""
import bpy
from bpy.app.translations import pgettext_iface as iface_

from . import store


COLUMNS = 10          # 한 줄에 10칸, 11번째부터 다음 줄(Maya 셸프처럼)
UNIT = 20.0           # Blender 버튼 기본 높이(픽셀, UI 배율 1 기준)


def _square_scale(context):
    """칸이 정사각형으로 보이도록 버튼 높이 배율 = 칸 너비 / 버튼 기본 높이."""
    region = getattr(context, "region", None)
    ui = context.preferences.system.ui_scale if getattr(context, "preferences", None) else 1.0
    if region is None or region.width <= 0:
        return 1.6
    usable = region.width - 30 * ui                     # 패널 안쪽 여백
    return max(1.0, min(4.0, (usable / COLUMNS) / (UNIT * ui)))


def draw_tabs(layout):
    """RISO 상단 탭처럼 — 지금 탭은 눌린 모양, 끝에 + (새 탭). 탭을 우클릭하면 이름 바꾸기."""
    row = layout.row(align=True)
    for i, t in enumerate(store.tabs()):
        row.operator("cueboard.tab_select", text=t["name"], translate=False,
                     depress=(i == store.active_index())).index = i
    row.operator("cueboard.tab_add", text="", icon='ADD')


def draw_board(layout, context):
    from . import icons
    draw_tabs(layout)
    cs = store.cues()
    grid = layout.column(align=True)
    scale = _square_scale(context)
    for start in range(0, len(cs), COLUMNS):
        row = grid.row(align=True)
        row.scale_y = scale
        for i in range(start, start + COLUMNS):
            if i >= len(cs):
                row.label(text="")                       # 빈 칸 — 마지막 줄도 칸 크기를 같게
                continue
            c = cs[i]
            icon_id = icons.image_icon_id(c.get("image"))
            if icon_id:
                op = row.operator("cueboard.cue_run", text="", icon_value=icon_id)
            elif c.get("icon"):
                op = row.operator("cueboard.cue_run", text="", icon=c["icon"])
            else:
                op = row.operator("cueboard.cue_run", text=c["name"], translate=False)
            op.index = i
    if not cs:
        layout.label(text=iface_("No cues yet"), icon='INFO')
    layout.operator("cueboard.cue_new", icon='ADD')
    # 큐를 편집 중인 텍스트가 열려 있으면 저장 버튼
    sp = getattr(context, "space_data", None)
    t = sp.text if sp is not None and sp.type == 'TEXT_EDITOR' else None
    if t is not None and t.get("cueboard"):
        layout.operator("cueboard.cue_update", icon='FILE_REFRESH').text = t.name


def cue_context_menu(self, context):
    """Blender 버튼 오른쪽 클릭 메뉴에 덧붙임 — 큐 버튼·탭 버튼일 때만 항목이 보인다."""
    op = getattr(context, "button_operator", None)
    ident = op.bl_rna.identifier if op is not None else ""
    if ident == "CUEBOARD_OT_tab_select":                 # 탭: 이름 바꾸기 · 이동 · 삭제
        i, n = op.index, len(store.tabs())
        layout = self.layout
        layout.separator()
        layout.operator("cueboard.tab_rename", icon='GREASEPENCIL').index = i
        left = layout.row()
        left.enabled = i > 0
        o = left.operator("cueboard.tab_move", text=iface_("Move Left"), icon='TRIA_LEFT')
        o.index, o.direction = i, -1
        right = layout.row()
        right.enabled = i < n - 1
        o = right.operator("cueboard.tab_move", text=iface_("Move Right"), icon='TRIA_RIGHT')
        o.index, o.direction = i, 1
        layout.operator("cueboard.tab_delete", icon='X').index = i
        return
    if ident != "CUEBOARD_OT_cue_run":
        return
    i = op.index
    n = len(store.cues())
    layout = self.layout
    layout.separator()
    layout.operator("cueboard.cue_edit", icon='TEXT').index = i
    layout.operator("cueboard.cue_rename", icon='GREASEPENCIL').index = i
    layout.operator("cueboard.cue_icon", icon='IMAGE_PLANE').index = i
    layout.operator("cueboard.cue_image", icon='IMAGE_DATA').index = i
    layout.operator("cueboard.cue_icon_clear", icon='PANEL_CLOSE').index = i
    up = layout.row()
    up.enabled = i > 0
    o = up.operator("cueboard.cue_move", text=iface_("Move Up"), icon='TRIA_UP')
    o.index, o.direction = i, -1
    down = layout.row()
    down.enabled = i < n - 1
    o = down.operator("cueboard.cue_move", text=iface_("Move Down"), icon='TRIA_DOWN')
    o.index, o.direction = i, 1
    layout.operator("cueboard.cue_delete", icon='X').index = i


def text_header(self, context):
    """Text Editor 헤더 — 큐 편집 중일 때만 '편집 중: 이름'과 저장 버튼."""
    from .ops import edit_target, is_dirty
    t = context.space_data.text
    tg = edit_target(t)
    if tg is None:
        return
    row = self.layout.row(align=True)
    mark = " *" if is_dirty(t) else ""                    # 저장 안 된 변경
    row.label(text=iface_("Editing: {}").format(f"{tg[0]} / {tg[1]}") + mark, icon='TEXT', translate=False)
    row.operator("cueboard.cue_save", icon='FILE_TICK')
    self.layout.separator()


class CUEBOARD_PT_view3d(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Cueboard"
    bl_label = "Cueboard"

    def draw(self, context):
        draw_board(self.layout, context)


class CUEBOARD_PT_text(bpy.types.Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Cueboard"
    bl_label = "Cueboard"

    def draw(self, context):
        draw_board(self.layout, context)


classes = (CUEBOARD_PT_view3d, CUEBOARD_PT_text)
