import asyncio
import os
import re
import subprocess
import imageio_ffmpeg
from edge_tts import Communicate

# 获取内置的 ffmpeg 路径，完全抛弃 pydub 和 ffprobe 依赖
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

DIALOGUE_TEXT = """
M: Do you think we should cut down the budget for the community art exhibition? 
W: No. The exhibition helps local artists get noticed and attracts many visitors. 
Q: What does the woman mean?
"""

OUTPUT_FILE = r"C:\Users\grace\VisualStudioProject\watermark-removal\5.mp3"
LIST_FILE = r"C:\Users\grace\VisualStudioProject\watermark-removal\file_list.txt"

VOICE_FEMALE = "en-US-AriaNeural"
VOICE_MALE = "en-US-ChristopherNeural"

async def main():
    lines = DIALOGUE_TEXT.strip().split("\n")
    temp_files = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 兼容 W, M, Q, Question 等前缀
        match = re.match(r"^(W|M|Q|Question)\s*[:：]\s*(.*)$", line, re.IGNORECASE)
        if not match:
            continue

        speaker, text = match.groups()
        speaker_upper = speaker.upper()

        # 根据角色选择声音（Q / Question 默认使用女声播报，可按需调整）
        if speaker_upper.startswith("W"):
            voice = VOICE_FEMALE
        elif speaker_upper.startswith("M"):
            voice = VOICE_MALE
        else:
            voice = VOICE_FEMALE  # 问题部分默认使用女声

        temp_file = os.path.join(r"C:\Users\grace\VisualStudioProject\watermark-removal", f"temp_{i}.mp3")
        temp_files.append(temp_file)

        print(f"正在生成 [{speaker_upper}]: {text}")
        communicate = Communicate(text, voice)
        await communicate.save(temp_file)

    if not temp_files:
        print("错误：没有匹配到任何对话内容。")
        return

    print("正在合并音频文件...")
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        for tf in temp_files:
            rel_name = os.path.basename(tf)
            f.write(f"file '{rel_name}'\n")

    cmd = [
        FFMPEG_EXE,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", LIST_FILE,
        "-c", "copy",
        OUTPUT_FILE
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"FFmpeg 拼接出错: {result.stderr}")
    else:
        print(f"对话音频生成成功，已保存至: {OUTPUT_FILE}")

    if os.path.exists(LIST_FILE):
        os.remove(LIST_FILE)
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    asyncio.run(main())