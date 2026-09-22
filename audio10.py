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
M: I just got the feedback from our supervisor. He's not satisfied with our project report at all.
W: Oh no! What happened? We spent three days polishing it.
M: We missed several key data statistics. We should have double-checked every detail before submission.
W: What a pity! I was too busy with the team arrangement and ignored the data part. We could have avoided this mistake.
M: Tough luck. Now we have to rewrite the whole report within tomorrow noon.
W: Boy! That's such a tight deadline. Do you have any idea to fix this quickly?
M:If I were you, I would sort out the latest industry data first and focus on the core content instead of minor details.
W: You said it! That's exactly what we need to do. I'll start sorting data right away.
M: By the way, I asked Lisa for help yesterday, but she refused to assist us.
W: Are you kidding? She promised to cooperate with our team last week!
M: Nope. She said she was fully occupied with her own tasks.
W: Well, fortunately, our new intern offered to help. She is super efficient.
M: Wow! That's terrific. Her work ability is really impressive.
W: You bet! She's my favorite intern in the whole department. I think we can finish the revision on time with her help. 
Question: What is the woman's attitude toward the new intern?
"""

OUTPUT_FILE = r"C:\Users\grace\VisualStudioProject\watermark-removal\10.mp3"
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