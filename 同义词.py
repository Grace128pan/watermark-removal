import os
import io
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

def remove_watermarks_bulletproof(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    out_doc = fitz.open()
    
    # 1. 物理删除前 2 页
    for _ in range(2):
        if len(doc) > 0:
            doc.delete_page(0)

    # 2. 遍历剩余页面
    for page in doc:
        # A. 顶部页眉区域强制白块覆盖
        rect = page.rect
        header_rect = fitz.Rect(0, 0, rect.width, rect.height * 0.08)
        page.add_redact_annot(header_rect, fill=(1, 1, 1))

        # B. 终极策略：锚定核心字 "张巍"，并向左右大幅扩展遮罩范围
        # 彻底解决因冒号、空格、文本拆分导致的漏网之鱼
        matches = page.search_for("张巍")
        for inst in matches:
            # 向左扩展 100 像素，向右扩展 80 像素，上下各扩展 6 像素
            expanded_box = fitz.Rect(
                inst.x0 - 100, 
                inst.y0 - 6, 
                inst.x1 + 80, 
                inst.y1 + 6
            )
            page.add_redact_annot(expanded_box, fill=(1, 1, 1))

        # 顺便清理其他可能残存的杂质关键词
        for kw in ["kaoshiguo", "EasyTV", "一手微信"]:
            for inst in page.search_for(kw):
                box = fitz.Rect(inst.x0 - 15, inst.y0 - 6, inst.x1 + 15, inst.y1 + 6)
                page.add_redact_annot(box, fill=(1, 1, 1))

        # 物理应用矢量层擦除
        page.apply_redactions(graphics=0, text=3)

        # C. 渲染为高清图像，执行“纯白底色化”处理（完美保留黑色正文与线条）
        dpi = 150
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes())).convert('RGB')
        
        data = np.array(img)
        r, g, b = data[:, :, 0].astype(int), data[:, :, 1].astype(int), data[:, :, 2].astype(int)
        
        # 计算平均亮度：仅保留深黑色正文与表格线条
        mean_val = (r + g + b) / 3.0
        text_mask = mean_val < 95
        
        cleaned_data = np.full_like(data, 255)
        cleaned_data[text_mask] = data[text_mask]

        # D. 将处理后的图像重新打包进 PDF 页面
        cleaned_img = Image.fromarray(cleaned_data.astype('uint8'))
        img_bytes = io.BytesIO()
        cleaned_img.save(img_bytes, format='PDF')
        img_doc = fitz.open("pdf", img_bytes.getvalue())
        out_doc.insert_pdf(img_doc)

    out_doc.save(output_pdf)
    out_doc.close()
    doc.close()

if __name__ == "__main__":
    target_file = "同义词意群汇总.pdf"
    output_dir = "./without"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    out_file = os.path.join(output_dir, target_file)

    if os.path.exists(target_file):
        print(f"正在执行核心字区域爆破清除：{target_file} ...")
        remove_watermarks_bulletproof(target_file, out_file)
        print(f"处理完成！干净文件已保存至: without/{target_file}")
    else:
        print(f"错误：未找到文件 '{target_file}'")