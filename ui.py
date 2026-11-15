# SPDX-License-Identifier: GPL-3.0-or-later
"""ui.py — 사이드바 패널(3D 뷰·Text Editor)과 큐 버튼 오른쪽 클릭 메뉴."""
import bpy
from bpy.app.translations import pgettext_iface as iface_

from . import store


COLUMNS = 10          # 한 줄에 10칸, 11번째부터 다음 줄(Maya 셸프처럼)
UNIT = 20.0           # Blender 버튼 기본 높이(픽셀, UI 배율 1 기준)
NAME_ROWS = 1.0       # 아이콘 큐 아래 이름 줄 높이(버튼 기본 높이 배수)
ICON_ROWS = 1.4       # 아이콘 버튼 높이 — 낮을수록 아이콘이 이름에 붙는다(클릭 영역도 이 높이)
BOX_PAD = 0.4         # 상자 안쪽 여백만큼 내용 높이를 줄여 칸이 정사각형에 가깝게(버튼 높이 배수)


def _square_scale(context):
    """칸이 정사각형으로 보이도록 버튼 높이 배율 = 칸 너비 / 버튼 기본 높이."""
    region = getattr(context, "region", None)
    ui = context.preferences.system.ui_scale if getattr(context, "preferences", None) else 1.0
    if region is None or region.width <= 0:
        return 1.6
    usable = region.width - 30 * ui                     # 패널 안쪽 여백
    return max(1.0, min(4.0, (usable / COLUMNS) / (UNIT * ui)))


def _cells(row, n):
    """줄을 n칸으로 똑같이 나눈다 — 버튼 내용(아이콘만·글자)과 상관없이 칸 폭이 같게.
    (그냥 row에 넣으면 글자 있는 버튼만 남는 폭을 나눠 가져 아이콘 버튼이 좁아진다)
    칸은 column — row 안에 넣으면 칸 폭이 버튼 내용(아이콘 크기)대로 줄어든다. column은 받은 폭을 꽉 채운다."""
    cells, cur = [], row
    for k in range(n - 1):
        sp = cur.split(factor=1.0 / (n - k), align=True)
        cells.append(sp.column(align=True))
        cur = sp.column(align=True)
    cells.append(cur)
    return cells


def _spacer(layout, rows):
    """세로 빈칸(버튼 높이 배수) — 너무 얇으면 넣지 않는다."""
    if rows >= 0.1:
        sp = layout.row()
        sp.scale_y = rows
        sp.label(text="")


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
    cell_h = max(scale - BOX_PAD, ICON_ROWS + NAME_ROWS)  # 상자 안 내용 높이 — 좁은 패널에서도 아이콘+이름이 들어가게
    for start in range(0, len(cs), COLUMNS):
        row = grid.row(align=True)                       # 줄 배율은 두지 않고 칸마다 준다(겹쳐 곱해지지 않게)
        for k, cell in enumerate(_cells(row, COLUMNS)):
            i = start + k
            col = cell                                   # 칸 = column(받은 폭을 꽉 채움)
            if i >= len(cs):
                col.scale_y = cell_h
                col.label(text="")                       # 빈 칸 — 마지막 줄도 칸 크기를 같게
                continue
            c = cs[i]
            icon_id = icons.image_icon_id(c.get("image"))
            box = col.box()                              # 칸 = 상자 하나(아이콘·이름을 한 상자 안에 두 줄로)
            inner = box.column(align=True)
            if icon_id or c.get("icon"):                 # 빈칸 · 아이콘(테두리 없는 실행 버튼) · 이름 · 빈칸
                # 아이콘은 버튼 세로 가운데에 그려지므로, 버튼을 낮게 해 이름 바로 위에 붙이고
                # 남는 높이는 위아래 빈칸으로 나눠 아이콘+이름 묶음을 상자 가운데에 둔다(상자 높이는 그대로)
                rest = (cell_h - ICON_ROWS - NAME_ROWS) / 2.0
                _spacer(inner, rest)
                top = inner.column(align=True)
                top.scale_y = ICON_ROWS
                if icon_id:
                    op = top.operator("cueboard.cue_run", text="", icon_value=icon_id, emboss=False)
                else:
                    op = top.operator("cueboard.cue_run", text="", icon=c["icon"], emboss=False)
                op.index = i
                cap = inner.row(align=True)
                cap.scale_y = NAME_ROWS
                cap.alignment = 'CENTER'
                cap.label(text=c["name"], translate=False)
                _spacer(inner, rest)
            else:                                        # 이름만 — 같은 상자 높이에 이름 버튼(테두리 없음)
                inner.scale_y = cell_h
                inner.operator("cueboard.cue_run", text=c["name"], translate=False, emboss=False).index = i
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
