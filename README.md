# VoiceToText 🎙️

> **Intel Core Ultra 7 258V (Lunar Lake)** の GPU / NPU を活用し、ローカル環境で高速・高精度に動画から日本語文字起こしを行うツールです。

![Intel Core Ultra](https://img.shields.io/badge/CPU-Intel%20Core%20Ultra%207%20258V-blue?style=flat-square&logo=intel)
![OpenVINO](https://img.shields.io/badge/AI%20Engine-OpenVINO%202026-teal?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🌟 概要

撮影済みの **MP4 動画ファイルや音声ファイル** を指定するだけで、**OpenVINO GenAI + OpenAI Whisper** を使ってローカル PC 内で文字起こしを実行します。

文字起こし結果は **NotebookLM** や **Gemini** にそのままアップロードして議事録・要約を作成できるよう、最適化されたフォーマット（`.txt` / `.md`）で自動保存されます。

---

## ✨ 主な特徴

- 🔒 **完全ローカル AI 推論**
  - クラウドへ音声を送信せず、PC 内の Intel Core Ultra (Arc GPU / NPU) のみで動作。
  - 最新の `OpenVINO/whisper-large-v3-turbo-fp16-ov` や `OpenVINO/whisper-small-fp16-ov` をサポート。

- 🎬 **動画からの音声自動抽出**
  - MP4, MKV, AVI, MOV などの動画ファイルをそのまま指定可能。
  - FFmpeg（組み込み）により、バックグラウンドで 16kHz モノラル WAV に自動変換。

- ⚡ **超高速処理 & 長尺対応**
  - Intel Arc GPU (140V) で実時間の **10倍以上（RTF ~0.09x）** の速度で文字起こし。
  - 音声を自動分割処理し、長時間動画も安定して処理（プログレスバー表示）。

- 📝 **NotebookLM / Gemini 連携に最適**
  - タイムスタンプ付きプレーンテキスト (`_文字起こし.txt`) と構造化 Markdown (`_文字起こし.md`) を同時出力。

---

## 🚀 使い方

### 1. 基本的な実行方法

```bash
python transcribe.py "C:\path\to\your_video.mp4"
```

### 2. ファイルをドラッグ＆ドロップして実行

引数なしで実行すると対話モードになります。動画ファイルをドラッグ＆ドロップして Enter キーを押すだけで起動します。

```bash
python transcribe.py
```

### 3. オプション指定

#### 🔹 高精度モデル (Whisper Large-v3-Turbo) で実行（推奨）
```bash
python transcribe.py "your_video.mp4" -m OpenVINO/whisper-large-v3-turbo-fp16-ov
```

#### 🔹 デバイスの指定 (GPU / NPU / CPU)
```bash
python transcribe.py "your_video.mp4" -d GPU
```
> ※ NPU を使用する場合は `-d NPU` を指定します。

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

- **OS**: Windows 11
- **SoC**: Intel Core Ultra 7 258V (Lunar Lake)
- **RAM**: 32 GB
- **AI Engine**: OpenVINO 2026 / OpenVINO GenAI
- **GPU**: Intel Arc Graphics 140V
