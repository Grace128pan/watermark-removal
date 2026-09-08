from docx import Document
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from pathlib import Path
import re


# ==============================
# 文件路径
# ==============================

input_docx = Path(
    r"C:\Users\grace\VisualStudioProject\watermark-removal\without\同义词意群汇总.docx"
)


output_pdf = input_docx.parent / "同义词意群汇总-精美版.pdf"


# ==============================
# 中文字体
# ==============================

font_path = r"C:\Windows\Fonts\msyh.ttc"

pdfmetrics.registerFont(
    TTFont("MicrosoftYaHei", font_path)
)


# ==============================
# 读取Word
# ==============================

doc = Document(input_docx)


items = []

current = None


for p in doc.paragraphs:

    text = p.text.strip()

    if not text:
        continue


    # 例如：
    # 1. 奇怪的
    match = re.match(
        r"(\d+)[\.、]\s*(.+)",
        text
    )

    if match:

        if current:
            items.append(current)

        current = {
            "number": match.group(1),
            "title": match.group(2),
            "words": []
        }

    else:

        if current:
            current["words"].append(text)


if current:
    items.append(current)



print("识别词条数量：", len(items))


# ==============================
# PDF样式
# ==============================


pdf = SimpleDocTemplate(
    str(output_pdf),
    pagesize=A4,
    rightMargin=50,
    leftMargin=50,
    topMargin=50,
    bottomMargin=50
)


styles = getSampleStyleSheet()


title_style = ParagraphStyle(
    "title",
    parent=styles["Normal"],
    fontName="MicrosoftYaHei",
    fontSize=13,
    leading=18,
    spaceAfter=8
)


word_style = ParagraphStyle(
    "words",
    parent=styles["Normal"],
    fontName="MicrosoftYaHei",
    fontSize=11,
    leading=18
)


line_style = ParagraphStyle(
    "line",
    parent=styles["Normal"],
    fontName="MicrosoftYaHei",
    fontSize=10
)



story = []


# ==============================
# 生成PDF
# ==============================

for item in items:

    # 分割线
    story.append(
        Paragraph(
            "━━━━━━━━━━━━━━",
            line_style
        )
    )


    story.append(
        Spacer(1,8)
    )


    # 中文标题
    story.append(
        Paragraph(
            f"{item['number']}. {item['title']}",
            title_style
        )
    )


    story.append(
        Spacer(1,8)
    )


    # 英文词
    words = " · ".join(item["words"])


    # 自动换行
    story.append(
        Paragraph(
            words,
            word_style
        )
    )


    story.append(
        Spacer(1,20)
    )


# 最后一条线

story.append(
    Paragraph(
        "━━━━━━━━━━━━━━",
        line_style
    )
)


pdf.build(story)


print("\n完成!")
print(output_pdf)