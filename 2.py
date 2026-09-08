import io
import os
import fitz  # PyMuPDF 库
from PIL import Image


def remove_pdf_watermark_perfectly():
    # 1. 路径定义
    base_dir = r"C:\Users\grace\VisualStudioProject\watermark-removal"
    input_file = os.path.join(base_dir, "填空机经1800题.pdf")
    output_dir = os.path.join(base_dir, "without")
    output_file = os.path.join(output_dir, "填空机经1800题.pdf")

    # 确保没有此文件夹就创建
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_file):
        print(f"错误：未找到输入文件 {input_file}")
        return

    print(f"正在读取 PDF 文件: {input_file}")
    doc = fitz.open(input_file)

    # 2. 去掉前 4 页（保留第 5 页及之后的内容）
    if len(doc) > 4:
        # doc.select(range(start, end))，索引从 0 开始
        doc.select(range(4, len(doc)))
        print(f"已成功删除前 4 页，当前剩余页数: {len(doc)}")

    # 3. 需精准定位并涂白（删除）的黑色打字的水印字符串
    # 为了解决个别题目后面的去不掉，我们使用一个非常宽的字符串列表，覆盖所有已知变体
    stubborn_typed_watermarks = [
        "【微信公众号：张巍老师GRE】",
        "【微信公众号：张巍GRE】",
        "微信公众号：张巍老师GRE",
        "微信公众号：张巍GRE",
        "微信公众号: 张巍老师GRE",
        "【 微信公众号：张巍老师GRE 】",
        "微信公众号 张巍老师GRE",
        "【微信公众号：张巍老师 GRE】",
        "微信公众号：张巍 老师GRE",
        "张巍老师GRE",
        "【微信公众号】",
        "：张巍老师",
    ]

    # 需精准定位并删除的文本关键词（用于页眉和页脚）
    header_keywords = [
        "张巍GRE",
        "填空机经1800题",
    ]
    footer_keywords = [
        "微信公众号：",
        "张巍老师GRE",
    ]

    new_doc = fitz.open()  # 用于保存清理后内容的文档

    print(
        "正在执行矢量级清理与白色背景净化（100% 灭绝粉橙色水印，精准消灭题目尾部打字）..."
    )

    # 4. 逐页处理：矢量级文本删除 + 图像级白色背景净化
    for idx, page in enumerate(doc):
        width = page.rect.width
        height = page.rect.height

        # ----------------------------------------------------
        # 策略 A：精准矢量级文本搜索与删除 (Redaction)
        # 此方法直接作用于 PDF 矢量对象，不伤排版，且清晰度最高
        # ----------------------------------------------------

        # A1：处理题目后面顽固的黑色打字水印【微信公众号：张巍老师GRE】
        for kw in stubborn_typed_watermarks:
            # search_for 能自动搜寻页面中的文本（包含隐藏或拆碎的字符）
            rects = page.search_for(kw)
            for rect in rects:
                # 添加擦除标注 (fill=(1, 1, 1)表示擦除区域统一填充白色)
                # 矢量删除底层内容，从而彻底清除文本和背景水印
                page.add_redact_annot(rect, fill=(1, 1, 1))

        # A2：处理页眉区域 (高度 0~50 pt)
        header_rect = fitz.Rect(0, 0, width, 50)
        # 获取顶部区域文本，检查是否包含关键词
        header_text = page.get_text("text", clip=header_rect)
        if any(kw in header_text for kw in header_keywords):
            # 将顶部页眉区域涂白抹除
            page.add_redact_annot(header_rect, fill=(1, 1, 1))

        # A3：处理页脚左侧公众号区域 (底部 45 pt 且左侧 70% 宽度)
        footer_rect = fitz.Rect(
            0, height - 45, width * 0.7, height
        )
        footer_text = page.get_text("text", clip=footer_rect)
        if any(kw in footer_text for kw in footer_keywords):
            # 将页脚左下角涂白抹除，保留右下角页码
            page.add_redact_annot(footer_rect, fill=(1, 1, 1))

        # 执行本页所有的擦除覆盖，并统一填充为白色 (1, 1, 1)
        # 底层文本被彻底删除，背景强制填充为纯白色
        page.apply_redactions()

        # ----------------------------------------------------
        # 策略 B：深度图像级颜色 threshold 处理 (纯白背景 + 净化橙色水印残影)
        # 策略 A 处理了黑色文本，这里清理颜色水印和非纯白色衬底
        # ----------------------------------------------------

        # 将 pre-cleaned 页面以高清晰度 (DPI 300) 渲染为图像
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # 进行像素级颜色过滤：将任何不属于深色文本的像素强制拉成纯白色
        # 这将完美去掉背景浅色水印，且将背景统一为纯白色
        filtered_img = img.convert("L")  # 转灰度
        # 凡是颜色不深（亮于 160）的像素全部归一为白色
        filtered_img = filtered_img.point(lambda p: 255 if p > 160 else 0)
        # 转回 RGB 以保持一致性
        filtered_img = filtered_img.convert("RGB")

        # 将处理后的高清图像插入到新页面中
        img_buf = io.BytesIO()
        filtered_img.save(img_buf, format="PNG")

        new_page = new_doc.new_page(width=width, height=height)
        new_page.insert_image(new_page.rect, stream=img_buf.getvalue())

        if (idx + 1) % 20 == 0 or (idx + 1) == len(doc):
            print(f"进度: 已处理 {idx + 1} / {len(doc)} 页")

    # 5. 保存去水印后的 PDF（Garbage=4 与 Deflate 用于清理残留垃圾对象并压缩体积）
    new_doc.save(output_file, garbage=4, deflate=True)
    new_doc.close()
    doc.close()

    print(f"\n完美处理完成！文件已成功保存在: \n{output_file}")


if __name__ == "__main__":
    remove_pdf_watermark_perfectly()