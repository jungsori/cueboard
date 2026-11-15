# SPDX-License-Identifier: GPL-3.0-or-later
"""
Cueboard — 한 번 누르면 실행되는 Python 큐(버튼)를 모아 두는 Blender 확장(Maya 셸프 같은 역할).
큐는 사용자 폴더의 JSON에 저장되어 모든 .blend에서 같다. 편집·이름·순서·삭제는 버튼 오른쪽 클릭.
"""
import bpy

from . import store, ops, ui, icons

# Blender 인터페이스 언어가 한국어일 때
_KO = {
    "Add Cue from Text": "텍스트로 큐 등록", "New Cue": "새 큐", "Run Cue": "큐 실행",
    "Edit Cue": "내용 편집", "Update Cue from Text": "텍스트로 큐 갱신", "Rename Cue": "이름 바꾸기",
    "Move Cue": "큐 이동", "Move Up": "위로", "Move Down": "아래로", "Delete Cue": "삭제",
    "No cues yet": "아직 큐가 없습니다", "Name": "이름", "Text": "텍스트",
    "Register a Text Editor script as a cue": "Text Editor의 스크립트를 큐로 등록합니다",
    "Add an empty cue (right-click it to edit or rename)": "빈 큐를 추가합니다(오른쪽 클릭으로 편집·이름 바꾸기)",
    "Run this cue (right-click for more)": "이 큐를 실행합니다(오른쪽 클릭으로 편집·정리)",
    "Open this cue in the Text Editor": "이 큐를 Text Editor에서 엽니다",
    "Save the edited text back into its cue": "편집한 텍스트를 큐에 저장합니다",
    "Rename this cue": "이 큐의 이름을 바꿉니다", "Move this cue up or down": "큐를 위아래로 옮깁니다",
    "Delete this cue": "이 큐를 지웁니다",
    "Set Icon": "아이콘 지정", "Set Image Icon": "이미지 아이콘 지정", "Clear Icon": "아이콘 지우기",
    "Choose a Blender icon for this cue": "Blender 아이콘을 골라 이 큐에 씁니다",
    "Use an image file (PNG, JPG) as this cue's icon": "이미지 파일(PNG, JPG)을 이 큐의 아이콘으로 씁니다",
    "Remove this cue's icon or image": "이 큐의 아이콘·이미지를 지웁니다",
    "Could not load the image": "이미지를 불러오지 못했습니다",
    "Save Cue": "큐 저장", "Save this text into its cue": "이 텍스트를 큐에 저장합니다",
    "Editing: {}": "편집 중: {}",
    "Select Tab": "탭 선택", "New Tab": "새 탭", "Rename Tab": "탭 이름 바꾸기",
    "Show this tab (right-click to rename)": "이 탭을 봅니다(오른쪽 클릭으로 이름 바꾸기)",
    "Add a tab (right-click it to rename)": "탭을 추가합니다(오른쪽 클릭으로 이름 바꾸기)",
    "Rename this tab": "이 탭의 이름을 바꿉니다",
    "Move Tab": "탭 이동", "Move Left": "왼쪽으로", "Move Right": "오른쪽으로", "Delete Tab": "탭 삭제",
    "Move this tab left or right": "탭을 왼쪽·오른쪽으로 옮깁니다",
    "Delete this tab and all its cues": "이 탭과 안의 큐를 모두 지웁니다",
}
translations = {"ko_KR": {}}
for en, ko in _KO.items():
    for ctx in ("*", "Operator"):
        translations["ko_KR"][(ctx, en)] = ko

_classes = ops.classes + ui.classes
_keymaps = []


def _add_keymap():
    """Text Editor에서 큐 편집 텍스트일 때만 Ctrl+S = 큐 저장(아니면 poll이 꺼져 원래 저장으로)."""
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is None:                                   # 백그라운드 실행 등
        return
    km = kc.keymaps.new(name="Text", space_type='TEXT_EDITOR')
    kmi = km.keymap_items.new("cueboard.cue_save", 'S', 'PRESS', ctrl=True)
    _keymaps.append((km, kmi))


def register():
    for c in _classes:
        bpy.utils.register_class(c)
    bpy.types.UI_MT_button_context_menu.append(ui.cue_context_menu)
    bpy.types.TEXT_HT_header.prepend(ui.text_header)          # 헤더 맨 앞(창을 열면 먼저 보이게)
    _add_keymap()
    bpy.app.translations.register(__name__, translations)
    store.reload()


def unregister():
    bpy.app.translations.unregister(__name__)
    bpy.types.UI_MT_button_context_menu.remove(ui.cue_context_menu)
    bpy.types.TEXT_HT_header.remove(ui.text_header)
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)
    icons.free()
