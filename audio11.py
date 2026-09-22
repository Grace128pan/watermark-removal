import asyncio
import os
import re
import subprocess
import imageio_ffmpeg
from edge_tts import Communicate

# 获取内置的 ffmpeg 路径，完全抛弃 pydub 和 ffprobe 依赖
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# 修复后的干净对话文本
DIALOGUE_TEXT = """
M: The dinner was amazing. The waiter was really attentive throughout the meal. Shall we leave a tip now?
W: Hmm, I'm a little short on cash. Could you lend me some money for the tip? I forgot to bring my wallet.
M: Don't look at me. Do you think I was made of money? I just paid for my own share of the dinner.
W: Oh, come on. I'll pay you back tomorrow. It's just a small amount.
M: Sorry. You know I usually manage my budget strictly. If you really need extra money, you could apply for a bank loan. Many people here rely on loans to cover daily expenses.
W: A bank loan for a tip? That sounds over the top. I thought tipping was optional.
M: Not really. Tipping is a local custom. People here are generous with tips because of sound social welfare and their personal financial plans. It's a way to recognize the service workers' hard work. Everyone should take responsibility for their own spending.
W: I get your point. You value self-reliance, right?
M: Exactly. I believe in individual effort. We shouldn't always count on others to help us out.

Question: What can we learn from the conversation?
"""

OUTPUT_FILE = r"C:\Users\grace\VisualStudioProject\watermark-removal\11.mp3"
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

        # 根据角色选择声音
        if speaker_upper.startswith("W"):
            voice = VOICE_FEMALE
        elif speaker_upper.startswith("M"):
            voice = VOICE_MALE
        else:
            voice = VOICE_FEMALE  # 问题部分默认使用女声

        temp_file = os.path.join(r"C:\Users\grace\VisualStudioProject\watermark-removal", f"temp_{i}.mp3")
        temp_files.append(temp_file)

        # 优化点：使用 SSML 标签将语速微微调慢（-5%），消除过快的“机械感”，听起来更自然流畅
        ssml_text = f"""
            
                {text}
            
        """

        print(f"正在生成 [{speaker_upper}]: {text}")
        # edge-tts 原生支持传入 SSML 文本
        communicate = Communicate(ssml_text, voice)
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