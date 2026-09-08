import io
import os
import fitz  # 来自 pymupdf
from PIL import Image, ImageDraw


def remove_watermark_binarization():
    # 1. 路径配置
    base_dir = r"C:\Users\grace\VisualStudioProject\watermark-removal"
    input_file = os.path.join(base_dir, "填空机经1800题.pdf")
    output_dir = os.path.join(base_dir, "without")
    output_file = os.path.join(output_dir, "填空机经1800题.pdf")

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_file):
        print(f"错误：未能找到输入文件 {input_file}")
        return

    print(f"正在读取文件: {input_file}")
    doc = fitz.open(input_file)

    # 2. 删去前 4 页（保留第 5 页及以后）
    if len(doc) > 4:
        doc.select(range(4, len(doc)))
        print(f"已成功删除前 4 页，剩余处理页数: {len(doc)}")

    new_doc = fitz.open()  # 创建输出 PDF

    print(
        "正在执行【像素级色彩二值化清洗】（100% 灭绝粉橙色水印，绝对保留黑色正文）..."
    )

    for idx, page in enumerate(doc):
        # 3. 将页面以 300 DPI 超高清渲染为图像
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        w, h = img.size

        # 4. 精准擦除页眉页脚（黑色公众号字样）
        draw = ImageDraw.Draw(img)
        # 涂白页眉区域（顶部 3.5% 高度：包含“张巍GRE 填空机经1800题”、“真经GRE”）
        draw.rectangle([0, 0, w, int(h * 0.035)], fill=(255, 255, 255))
        # 涂白页脚左侧（底部 3.5% 高度、左侧 68% 宽度：包含“微信公众号：张巍老师GRE”，保留右下角页码）
        draw.rectangle(
            [0, int(h * 0.965), int(w * 0.68), h], fill=(255, 255, 255)
        )

        # 5. 色彩二值化核心（Pixel-Level Thresholding）
        # 转为灰度图：黑色正文灰度值 ~0-80，浅橙/浅粉背景水印灰度值 ~180-230
        gray = img.convert("L")

        # 阈值判定：凡是灰度值 > 140 的浅色（橙色水印/背景）直接设为 255 (纯白)；
        # 凡是灰度值 <= 140 的深色（正文文字/表格线/下划线）设为 0 (纯黑)
        binary = gray.point(lambda p: 255 if p > 140 else 0)

        # 转回 RGB 模式
        clean_img = binary.convert("RGB")

        # 6. 将清洗后的超清图像重构回 PDF
        img_buf = io.BytesIO()
        clean_img.save(img_buf, format="PNG", compress_level=1)

        new_page = new_doc.new_page(
            width=page.rect.width, height=page.rect.height
        )
        new_page.insert_image(new_page.rect, stream=img_buf.getvalue())

        if (idx + 1) % 20 == 0 or (idx + 1) == len(doc):
            print(f"进度: 已完成 {idx + 1} / {len(doc)} 页")

    # 7. 保存导出
    new_doc.save(output_file, deflate=True)
    new_doc.close()
    doc.close()

    print(f"\n成功处理完成！无水印高清文件已保存在:\n{output_file}")


if __name__ == "__main__":
    remove_watermark_binarization()