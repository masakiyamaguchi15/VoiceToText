#!/usr/bin/env python3
"""
OpenVINO Local AI Whisper 音声認識・文字起こしスクリプト
Intel Core Ultra (Lunar Lake / Meteor Lake) 最適化版

機能:
1. MP4 などの動画ファイルから ffmpeg を用いて 16kHz モノラル WAV 音声を抽出
2. OpenVINO GenAI (WhisperPipeline) を使い GPU / NPU / CPU で高速ローカル文字起こし
3. タイムスタンプ付きのテキストおよび Markdown ファイルを出力 (NotebookLM / Gemini 議事録作成に最適化)
"""

import os
import sys

# Windows コンソールでの UTF-8 出力を設定
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse
import time
import subprocess
import numpy as np
import soundfile as sf
import imageio_ffmpeg
from huggingface_hub import snapshot_download
from tqdm import tqdm

try:
    import openvino_genai as ov_genai
except ImportError:
    print("エラー: openvino_genai がインストールされていません。")
    print("`pip install openvino-genai openvino-tokenizers openvino` を実行してください。")
    sys.exit(1)


def extract_audio_from_video(video_path: str, output_wav_path: str) -> str:
    """
    ffmpeg を利用して動画ファイルから 16kHz モノラル WAV 音声を抽出
    """
    print(f"[1/4] 動画ファイルから音声を抽出中...: {video_path}")
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe,
        "-y",               # 既存ファイルを上書き
        "-i", video_path,   # 入力ファイル
        "-ar", "16000",     # サンプリングレート 16kHz
        "-ac", "1",         # モノラル (1チャンネル)
        "-c:a", "pcm_s16le",# PCM 16bit LE
        output_wav_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"FFmpeg エラー:\n{result.stderr.decode('utf-8', errors='ignore')}")
        raise RuntimeError("音声抽出に失敗しました。ファイル形式を確認してください。")
    
    print(f"   -> 音声ファイルを生成しました: {output_wav_path}")
    return output_wav_path


def format_timestamp(seconds: float) -> str:
    """秒数を hh:mm:ss 形式に変換"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def transcribe_audio(
    wav_path: str,
    model_id: str = "OpenVINO/whisper-large-v3-turbo-fp16-ov",
    device: str = "GPU",
    chunk_seconds: int = 30,
    language: str = "<|ja|>"
):
    """
    OpenVINO WhisperPipeline による文字起こし処理
    """
    print(f"[2/4] OpenVINO Whisper モデルの準備中...")
    print(f"      - モデル: {model_id}")
    print(f"      - デバイス: {device} (Intel Core Ultra)")
    
    # 1. モデルのダウンロード / キャッシュ確認
    try:
        model_dir = snapshot_download(repo_id=model_id)
    except Exception as e:
        print(f"モデルのダウンロードに失敗しました: {e}")
        # フォールバックとして whisper-small も試す
        fallback_model = "OpenVINO/whisper-small-fp16-ov"
        print(f"フォールバックモデル ({fallback_model}) を試行します...")
        model_dir = snapshot_download(repo_id=fallback_model)

    # 2. OpenVINO WhisperPipeline の初期化
    print(f"      - OpenVINO パイプラインを初期化中 ({device})...")
    start_init = time.time()
    pipe = ov_genai.WhisperPipeline(model_dir, device)
    init_time = time.time() - start_init
    print(f"   -> パイプライン初期化完了 ({init_time:.2f} 秒)")

    # 3. 音声ファイルの読み込み (float32, 16kHz)
    print(f"[3/4] 音声データをロード中...")
    audio_data, sr = sf.read(wav_path, dtype="float32")
    if sr != 16000:
        raise ValueError(f"サンプリングレートが 16kHz ではありません ({sr}Hz)")

    total_samples = len(audio_data)
    total_seconds = total_samples / sr
    print(f"   -> 総音声時間: {format_timestamp(total_seconds)} ({total_seconds:.1f} 秒)")

    # 4. 音声を分割して推論実行
    print(f"[4/4] 文字起こしを実行中...")
    chunk_samples = chunk_seconds * sr
    num_chunks = int(np.ceil(total_samples / chunk_samples))

    config = pipe.get_generation_config()
    config.language = language
    config.task = "transcribe"

    transcripts = []
    
    start_transcribe = time.time()
    
    with tqdm(total=num_chunks, desc="文字起こし進捗", unit="個") as pbar:
        for i in range(num_chunks):
            chunk_start = i * chunk_samples
            chunk_end = min((i + 1) * chunk_samples, total_samples)
            chunk_audio = audio_data[chunk_start:chunk_end]
            
            # 短すぎる無音区間のスキップチェック (振幅が極端に小さい場合)
            if len(chunk_audio) < sr * 0.5:
                pbar.update(1)
                continue
                
            # リスト型 float32 に変換して OpenVINO GenAI に入力
            raw_speech = chunk_audio.tolist()
            result = pipe.generate(raw_speech, config)
            
            text = result.texts[0].strip()
            
            t_start_sec = chunk_start / sr
            t_end_sec = chunk_end / sr
            time_str = f"[{format_timestamp(t_start_sec)} -> {format_timestamp(t_end_sec)}]"
            
            if text:
                transcripts.append({
                    "start": t_start_sec,
                    "end": t_end_sec,
                    "time_str": time_str,
                    "text": text
                })
            
            pbar.update(1)

    elapsed = time.time() - start_transcribe
    rtf = elapsed / total_seconds if total_seconds > 0 else 0
    print(f"\n   -> 文字起こし完了! (処理時間: {elapsed:.2f} 秒, Real Time Factor: {rtf:.2f}x)")
    
    return transcripts, total_seconds, elapsed


def save_results(transcripts, input_video_path, output_txt_path=None):
    """
    結果をテキストファイルおよび NotebookLM 向け Markdown ファイルとして保存
    """
    base_name = os.path.splitext(input_video_path)[0]
    
    if not output_txt_path:
        output_txt_path = f"{base_name}_文字起こし.txt"
    
    output_md_path = f"{base_name}_文字起こし.md"

    # 1. プレーンテキスト出力 (NotebookLM / Prompt 添付用)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(f"# 音声文字起こし結果: {os.path.basename(input_video_path)}\n\n")
        for item in transcripts:
            f.write(f"{item['time_str']} {item['text']}\n")

    # 2. Markdown 構造化出力 (NotebookLM 議事録生成用)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(f"# 動画文字起こしノート\n\n")
        f.write(f"- **元ファイル**: `{os.path.basename(input_video_path)}`\n")
        f.write(f"- **文字起こし日時**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## タイムスタンプ付き文字起こし本文\n\n")
        for item in transcripts:
            f.write(f"### {item['time_str']}\n{item['text']}\n\n")

    print(f"\n[保存完了]")
    print(f" - テキスト形式 : {os.path.abspath(output_txt_path)}")
    print(f" - Markdown形式: {os.path.abspath(output_md_path)}")


def main():
    parser = argparse.ArgumentParser(
        description="Intel Core Ultra Local AI (OpenVINO) を使った MP4 動画文字起こしツール"
    )
    parser.add_argument("input_file", type=str, nargs="?", help="文字起こし対象の動画/音声ファイル (例: meeting.mp4)")
    parser.add_argument("-d", "--device", type=str, default="GPU", choices=["GPU", "NPU", "CPU", "AUTO"],
                        help="推論を実行する OpenVINO デバイス (デフォルト: GPU)")
    parser.add_argument("-m", "--model", type=str, default="OpenVINO/whisper-large-v3-turbo-fp16-ov",
                        help="使用する OpenVINO Whisper モデル ID (デフォルト: OpenVINO/whisper-large-v3-turbo-fp16-ov)")
    parser.add_argument("-o", "--output", type=str, default=None, help="出力テキストファイルのパス")
    parser.add_argument("--chunk", type=int, default=30, help="分割処理の1区間の長さ(秒) (デフォルト: 30)")
    
    args = parser.parse_args()

    # 引数なしで起動された場合のインタラクティブモード
    input_file = args.input_file
    if not input_file:
        print("=== Intel Core Ultra (OpenVINO) Whisper 文字起こしアプリ ===")
        input_file = input("動画または音声ファイルのパスを入力してください (例: video.mp4): ").strip('"\'')
        if not input_file:
            print("エラー: ファイルが指定されていません。")
            sys.exit(1)

    if not os.path.exists(input_file):
        print(f"エラー: 指定されたファイルが存在しません: {input_file}")
        sys.exit(1)

    # 一時 WAV ファイルの作成
    temp_wav = f"temp_{int(time.time())}.wav"

    try:
        # 1. 音声抽出
        extract_audio_from_video(input_file, temp_wav)

        # 2. 文字起こし
        transcripts, total_sec, elapsed = transcribe_audio(
            wav_path=temp_wav,
            model_id=args.model,
            device=args.device,
            chunk_seconds=args.chunk
        )

        # 3. 結果の保存
        save_results(transcripts, input_file, args.output)

        print("\n=== 文字起こし処理が正常に完了しました！ ===")
        print("このファイルを NotebookLM または Gemini にアップロードして、議事録や要約を作成してください。")

    finally:
        # 一時ファイルの削除
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass


if __name__ == "__main__":
    main()
