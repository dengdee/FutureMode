import os
import wave
import pyttsx3
import subprocess


OUTPUT_DIR = "./app/audio"
TEMP_FILE = os.path.join(OUTPUT_DIR, "hello_temp.wav")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "hello.wav")

TEXT = "Hello, this is Proximate AI"


def convert_to_24khz_mono(input_file, output_file):
    """
    使用 ffmpeg 將音訊轉成：
    - 24000 Hz
    - Mono
    - 16-bit PCM
    """

    command = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-ar", "24000",
        "-ac", "1",
        "-sample_fmt", "s16",
        output_file,
    ]

    subprocess.run(command, check=True)


def check_wav(filename):
    with wave.open(filename, "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.getnframes()
        duration = frames / sample_rate

        print("===== WAV Info =====")
        print(f"File        : {filename}")
        print(f"Channels    : {channels}")
        print(f"Sample width: {sample_width * 8} bit")
        print(f"Sample rate : {sample_rate} Hz")
        print(f"Duration    : {duration:.2f} sec")

        if channels != 1:
            raise ValueError("音訊不是 Mono")

        if sample_width != 2:
            raise ValueError("音訊不是 16-bit")

        if sample_rate != 24000:
            raise ValueError("Sample rate 不是 24000 Hz")

        print("格式符合 Meeting BaaS input audio")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("正在產生語音...")
    
    engine = pyttsx3.init()

    # 語速
    engine.setProperty("rate", 150)

    # 音量
    engine.setProperty("volume", 1.0)

    engine.save_to_file(TEXT, TEMP_FILE)
    engine.runAndWait()

    print("TTS 產生完成")

    print("正在轉換成 Meeting BaaS 格式...")

    convert_to_24khz_mono(
        TEMP_FILE,
        OUTPUT_FILE
    )

    os.remove(TEMP_FILE)

    check_wav(OUTPUT_FILE)

    print()
    print("完成！")
    print(f"音訊檔：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()