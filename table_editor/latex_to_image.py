import os
import glob
from pylatex import Document, NoEscape
from pdf2image import convert_from_path
from datasets import load_dataset


# 加载 ArXiv 表格数据集（可以选 staghado/ArXiv-tables 或 neulab/latex-table）
dataset = load_dataset("staghado/ArXiv-tables") 

# 自动清理之前生成的中间文件
for ext in ["aux", "log", "fls", "pdf"]:
    for f in glob.glob(f"outputs/*.%s" % ext):
        os.remove(f)

def save_latex_as_image(latex_str, outname="outputs/output"):
    """
    将 LaTeX 表格代码编译为 PNG 图像。
    参数:
        latex_str: 一个完整的 LaTeX 表格字符串
        outname: 输出文件名（不带后缀）
    """
    # 创建输出目录
    os.makedirs("outputs", exist_ok=True)

    # 创建 LaTeX 文档对象
    doc = Document()
    doc.packages.append(NoEscape(r'\usepackage{float}'))   # 支持 [H]
    doc.packages.append(NoEscape(r'\usepackage{booktabs}'))  # 添加表格美化包
    doc.packages.append(NoEscape(r'\usepackage{graphicx}'))  # 支持 \resizebox
    doc.packages.append(NoEscape(r'\usepackage{multirow}'))  # 支持 \multirow
    doc.packages.append(NoEscape(r'\usepackage{makecell}'))  # 支持 \makecell
    doc.packages.append(NoEscape(r'\usepackage{cite}'))      # 支持 \cite 避免编译错误
    doc.packages.append(NoEscape(r'\usepackage{threeparttable}'))
    doc.packages.append(NoEscape(r'\usepackage{xcolor}'))
    doc.packages.append(NoEscape(r'\usepackage{amssymb}'))  # for \checkmark
    doc.packages.append(NoEscape(r'\usepackage{hyperref}')) # for \sref, \figref
    doc.packages.append(NoEscape(r'\usepackage{textcomp}')) # for \text{}
    # 添加 specialcell 宏定义
    doc.preamble.append(NoEscape(r'\newcommand{\specialcell}[2][c]{\begin{tabular}[#1]{@{}c@{}}#2\end{tabular}}'))

    # 自动补全缺失结构（按嵌套顺序）
    if "\\begin{tabular" in latex_str and "\\end{tabular}" not in latex_str:
        latex_str += "\n\\end{tabular}"
    if "\\begin{table" in latex_str and "\\end{table}" not in latex_str:
        latex_str += "\n\\end{table}"
    if "\\begin{threeparttable}" in latex_str and "\\end{threeparttable}" not in latex_str:
        latex_str += "\n\\end{threeparttable}"
    doc.append(NoEscape(latex_str))  # 加入表格内容

    # 生成 PDF 文件
    doc.generate_pdf(outname, clean_tex=True)

    # 将 PDF 转为 PNG 图像
    images = convert_from_path(f"{outname}.pdf", poppler_path="/opt/local/bin")
    images[0].save(f"{outname}.png", "PNG")
    print(f"图像保存成功：{outname}.png")

def batch_render_tables(dataset, start=0, end=10):
    # 要批量处理 N 条数据
    for i in range(start, end):  # 前 10 个样本
        latex_str = dataset["train"][i]["latex_content"]
        if "\\begin{tabular}" in latex_str and "\\end{tabular}" in latex_str and "\\begin{table}" in latex_str and "\\end{table}" in latex_str:
            print(f"第 {i} 条是表格，开始渲染图像...")
            try:
                save_latex_as_image(latex_str, outname=f"outputs/real_table_{i}")
            except Exception as e:
                print(f"❌ 第 {i} 条渲染失败：{e}")
                with open(f"outputs/real_table_{i}_error.tex", "w") as f:
                    f.write(latex_str)
                print(f"⚠️ 已保存失败的 LaTeX 源码为 outputs/real_table_{i}_error.tex")
        else:
            print(f"第 {i} 条表格结构不完整（缺少 table 或 tabular 结构），跳过")


# 看看每条数据有哪些字段
print(dataset["train"].column_names)

if __name__ == "__main__":
    dataset = load_dataset("staghado/ArXiv-tables")
    batch_render_tables(dataset, start=0, end=10)
    print("图像生成完毕")