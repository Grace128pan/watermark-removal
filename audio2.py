import asyncio
import os
import re
import subprocess
import imageio_ffmpeg
from edge_tts import Communicate

# 获取内置的 ffmpeg 路径，完全抛弃 pydub 和 ffprobe 依赖
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

DIALOGUE_TEXT = """
W: Our topic today is about something that foreigners nearly always say when they visit Britain. It's "Why are the British so cold?" And they're talking about the British personality—the famous British "reserve." It means that we aren't very friendly... we aren't very open.
M: So do you think it's true?
W: It's a difficult one. So many people who visit Britain say it's difficult to make friends with British people. They say we're cold, reserved, unfriendly...
M: I think it's true. Look at Americans or Australians. They speak the same language, but they're much more open. And you see it when you travel. People—I mean strangers—speak to you on the street or on the train. British people seldom speak on the train, or the bus. Not in London, anyway.
W: "Not in London." That's it. Capital cities are full of tourists and are never friendly. People are different in other parts of the country.
M: Not completely. I met a woman once, an Italian. She'd been working in Manchester for two years, and no one—not one of her colleagues—had ever invited her to their home. They were friendly to her at work, but nothing else. She couldn't believe it. She said that would never happen in Italy.
W: You know what they say—"an Englishman's home is his castle." It's really difficult to get inside.
M: Yeah. It's about being private. You go home to your house and your garden and you close the door. It's your place.
W: That's why the British don't like flats. They prefer to live in houses.
M: That's true.
"""

OUTPUT_FILE = r"C:\Users\grace\VisualStudioProject\watermark-removal\2.mp3"
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

        match = re.match(r"^(W|M)\s*[:：]\s*(.*)$", line, re.IGNORECASE)
        if not match:
            continue

        speaker, text = match.groups()
        voice = VOICE_FEMALE if speaker.upper() == "W" else VOICE_MALE
        temp_file = os.path.join(r"C:\Users\grace\VisualStudioProject\watermark-removal", f"temp_{i}.mp3")
        temp_files.append(temp_file)

        print(f"正在生成 [{speaker.upper()}]: {text}")
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