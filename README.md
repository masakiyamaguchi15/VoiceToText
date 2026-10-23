# VoiceToText 🎙️

> **Intel Core Ultra (Arc GPU / NPU)** および **AMD Ryzen (マルチコア CPU)** を活用し、ローカル環境で高速・高精度に動画・音声ファイルから日本語文字起こしを行うツールです。

![Intel Core Ultra](https://img.shields.io/badge/CPU-Intel%20Core%20Ultra%207%20258V-blue?style=flat-square&logo=intel)
![AMD Ryzen](https://img.shields.io/badge/CPU-AMD%20Ryzen%207%207735HS-orange?style=flat-square&logo=amd)
![OpenVINO](https://img.shields.io/badge/AI%20Engine-OpenVINO%202026-teal?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🌟 概要

撮影済みの **MP4 動画ファイルや音声ファイル** を指定するだけで、**OpenVINO GenAI + OpenAI Whisper** を使ってローカル PC 内で文字起こしを実行します。

お使いの PC 環境（Intel / AMD）を**自動検出**し、最適なデバイス（Intel Arc GPU または Ryzen マルチコア CPU）で文字起こしを実行します。

文字起こし結果は **NotebookLM** や **Gemini** にそのままアップロードして議事録・要約を作成できるよう、最適化されたフォーマット（`.txt` / `.md`）で自動保存されます。

---

## ✨ 主な特徴

- 🔒 **完全ローカル AI 推論**
  - クラウドへ音声を送信せず、ローカル PC 内のみで完結。
  - 最新の `OpenVINO/whisper-large-v3-turbo-fp16-ov` や `OpenVINO/whisper-small-fp16-ov` をサポート。

- 💻 **Intel & AMD マルチプラットフォーム自動最適化**
  - **Intel 機 (Core Ultra 258V 等)**: Intel Arc GPU (140V) や NPU を自動検出し、実時間の10倍以上（RTF ~0.09x）の超高速推論。
  - **AMD 機 (Ryzen 7 7735HS 等)**: 8コア/16スレッドの CPU 並列処理を自動選択。
  - デバイス自動判別（`AUTO`）を標準搭載しているため、マシンごとのオプション変更なしでそのまま実行可能。

- 🎬 **動画からの音声自動抽出**
  - MP4, MKV, AVI, MOV などの動画ファイルをそのまま指定可能。
  - FFmpeg（組み込み）により、バックグラウンドで 16kHz モノラル WAV に自動変換。

- ⚡ **長尺動画の安定処理**
  - 音声を自動分割処理し、長時間動画もメモリを圧迫せず安定処理（プログレスバー表示）。

- 📝 **NotebookLM / Gemini 連携に最適**
  - タイムスタンプ付きプレーンテキスト (`_文字起こし.txt`) と、実行環境・日時のメタデータ付き Markdown (`_文字起こし.md`) を同時出力。

---

## 🚀 使い方

### 1. 基本的な実行方法 (自動最適化)

Intel 機でも AMD 機でも、同じコマンドで自動的に最適な推論デバイスが選択されます。

```bash
python transcribe.py "C:\path\to\your_video.mp4"
```

### 2. ファイルをドラッグ＆ドロップして実行

引数なしで実行すると対話モードになります。画面上に検出されたデバイス名が表示され、動画ファイルをドラッグ＆ドロップして Enter キーを押すだけで起動します。

```bash
python transcribe.py
```

### 3. オプション指定

#### 🔹 推論デバイスの手動指定 (`AUTO` / `GPU` / `NPU` / `CPU`)
デフォルトは `AUTO`（自動判定）ですが、明示的に指定することも可能です。
```bash
# Intel Arc GPU を明示指定 (Intel 機向け)
python transcribe.py "your_video.mp4" -d GPU

# NPU を明示指定 (Intel NPU 向け)
python transcribe.py "your_video.mp4" -d NPU

# マルチコア CPU を明示指定 (AMD Ryzen または Intel CPU)
python transcribe.py "your_video.mp4" -d CPU
```
> ※ AMD 環境で `-d GPU` を誤って指定した場合でも、自動的に CPU にフォールバックして文字起こしを継続します。

#### 🔹 モデルの指定
```bash
# Whisper Large-v3-Turbo (デフォルト・推奨・高精度)
python transcribe.py "your_video.mp4" -m OpenVINO/whisper-large-v3-turbo-fp16-ov

# Whisper Small (より軽量・高速)
python transcribe.py "your_video.mp4" -m OpenVINO/whisper-small-fp16-ov
```

#### 🔹 出力ファイル名の指定
```bash
python transcribe.py "your_video.mp4" -o "meeting_result.txt"
```

---

## 📋 処理フロー & NotebookLM への連携

1. **文字起こし実行**  
   `python transcribe.py <動画.mp4>` を実行すると、同じフォルダに以下のファイルが自動作成されます。
   - `<動画名>_文字起こし.txt`
   - `<動画名>_文字起こし.md`

2. **NotebookLM へアップロード**  
   [NotebookLM](https://notebooklm.google.com/) のソース追加画面で、生成された `.md` または `.txt` ファイルをアップロードします。

3. **議事録・要約の生成**  
   NotebookLM で以下のようなプロンプトを入力すれば、一瞬で高品質な議事録が作成できます！

> [!TIP]
> **NotebookLM おすすめプロンプト例:**  
> 「この文字起こしテキストから、主要なアジェンダ、決定事項、およびアクションアイテムを含む議事録と要約を作成してください。」

---

## 💻 動作検証環境

| 項目 | Intel 機 (ThinkPad X1 Carbon) | AMD 機 (Ryzen ミニPC / ノート) |
| :--- | :--- | :--- |
| **SoC / CPU** | Intel Core Ultra 7 258V (Lunar Lake) | AMD Ryzen 7 7735HS (8C / 16T) |
| **GPU** | Intel Arc Graphics 140V | AMD Radeon 680M Graphics |
| **RAM** | 32 GB | 32 GB |
| **OS** | Windows 11 | Windows 11 |
| **推論デバイス** | GPU (`AUTO` 判定) | CPU (`AUTO` 判定) |
| **AI Engine** | OpenVINO 2026 / OpenVINO GenAI | OpenVINO 2026 / OpenVINO GenAI |

