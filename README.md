# Cueboard

**One-click Python cues for any workflow** — a shelf for Blender, like Maya's shelf.

Register any Python script as a button (a *cue*) and run it with one click from the sidebar.

- Blender 5.0 or later
- License: GPL-3.0-or-later
- Maintainer: Sori

## Features

- **Cueboard panel** in the sidebar (`N`) of the 3D View and the Text Editor
- **Add a cue from a Text Editor script**, or add an empty cue and write it later
- **Tabs** to group cues — right-click a tab to rename, move or delete it
- **Right-click a cue** to edit it in the Text Editor, rename, move, delete, or set an icon
- **Icons**: a Blender icon or your own image (PNG, JPG)
- **Edit and save**: open a cue in the Text Editor and press `Ctrl+S` to save it back into the cue
- Cues are saved in your **user folder**, so they are the same in every .blend file
- Korean interface when Blender's language is set to Korean

## Install

- **Blender Extensions**: search for *Cueboard* in *Edit › Preferences › Get Extensions*
- **From a file**: download the zip from Releases, then *Edit › Preferences › Get Extensions › ⌄ › Install from Disk*

## A note on running code

A cue runs the Python code that you wrote or registered yourself, just like *Run Script* in the Text Editor.
Cues are stored in your user folder (not inside .blend files) and run only when you click them.
Only add code you trust.

## Reporting issues

Please open an [issue](../../issues) with your Blender version and the steps to reproduce.

---

## 한국어

**Cueboard**는 Maya 셸프처럼, Python 스크립트를 버튼(큐)으로 등록해 실행하는 Blender 에드온입니다.

- 3D 뷰와 Text Editor의 사이드바(`N`)에 Cueboard 패널
- Text Editor의 스크립트를 큐로 등록하거나, 빈 큐를 만들어 나중에 작성
- 탭으로 큐를 묶음 — 탭을 오른쪽 클릭해 이름 바꾸기·이동·삭제
- 큐를 오른쪽 클릭해 편집·이름 바꾸기·이동·삭제·아이콘 지정(Blender 아이콘 또는 PNG·JPG 이미지)
- Text Editor에서 큐를 편집하고 `Ctrl+S`로 큐에 다시 저장
- 큐는 사용자 폴더에 저장되어 모든 .blend 파일에서 같음
- Blender 언어가 한국어면 화면도 한국어

큐는 직접 작성하거나 등록한 코드만 실행합니다. 믿을 수 있는 코드만 등록해 주세요.
