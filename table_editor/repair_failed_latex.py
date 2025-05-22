import os
import re
from latex_to_image import save_latex_as_image

def repair_latex_autofix(latex: str) -> str:
    """
    Attempt to fix common LaTeX issues in table source strings.
    """
    # Remove unsupported macros or undefined commands
    latex = re.sub(r'\\(boxit|boxittwo|boxitthree)\{.*?\}\{.*?\}', '', latex)
    latex = re.sub(r'\\smCT', '', latex)
    latex = re.sub(r'\\text\{(.*?)\}', r'\1', latex)

    # Remove more undefined or custom commands
    latex = re.sub(r'\\[a-zA-Z@]+(?:\s*{[^}]*})*', '', latex)

    # Extend \text{} removal logic
    latex = re.sub(r'\$\\text\{(.*?)\}\$', r'\1', latex)  # remove inline math \text
    latex = re.sub(r'\\text\{(.*?)\}', r'\1', latex)

    # Fix known math symbol issues
    latex = latex.replace(r'\Y', r'Y')
    latex = latex.replace(r'\bar{\Y}', r'\bar{Y}')
    latex = latex.replace(r'\mathcal{X}', r'\mathcal{X}')

    # Remove broken or unmatched commands
    latex = re.sub(r'\\[a-zA-Z]+\s*$', '', latex)

    # Replace problematic tilde characters with spaces
    latex = latex.replace('~', ' ')

    # Generalize color command removal
    latex = re.sub(r'\\color\{[^\}]*\}', '', latex)

    return latex

error_dir = "outputs"
error_files = [f for f in os.listdir(error_dir) if f.endswith("_error.tex")]

success_log_path = os.path.join(error_dir, "success_tables.txt")
if os.path.exists(success_log_path):
    with open(success_log_path, "r") as f:
        success_set = set(line.strip() for line in f)
else:
    success_set = set()

print(f"Found {len(error_files)} error files to process.\n")

for fname in error_files[:10]:  # 只处理前10条
    fixed_name = fname.replace("_error.tex", "_fixed.tex")
    if fixed_name in success_set:
        print(f"Skipping already successful: {fixed_name}")
        continue

    path = os.path.join(error_dir, fname)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # === 清洗非法控制字符 ===
    content = ''.join(c for c in content if c == '\n' or c >= ' ')
    # === 调用修复函数 ===
    content = repair_latex_autofix(content)

    # === 自动补全结构 ===
    if "\\begin{table" in content and "\\end{table}" not in content:
        if "\\end{tabular}" in content:
            if not re.search(r"\\end{tabular}.*?\\end{table}", content, re.DOTALL):
                content = re.sub(r"(\\end{tabular})", r"\1\n\\end{table}", content, count=1)
        else:
            if "\\begin{tabular" not in content:
                content = re.sub(r"\\begin{table}(\[.*?\])?", r"\\begin{table}\1\n\\begin{tabular}{c}\nPLACEHOLDER\\\\\n\\end{tabular}\n\\end{table}", content, count=1)
    if "\\end{document}" not in content:
        content += "\n\\end{document}"

    # 修复常见 LaTeX 错误
    content = content.replace(r"$\Gamma_{\Y", r"$\Gamma_{\mathcal{Y}")
    content = content.replace(r"$\Gamma_{\bar{\Y", r"$\Gamma_{\bar{\mathcal{Y}")
    if "ForestGreen" in content and "\\definecolor{ForestGreen}" not in content:
        content = "\\definecolor{ForestGreen}{rgb}{0.13, 0.55, 0.13}\n" + content

    # 保存修复版本
    fixed_name = fname.replace("_error.tex", "_fixed.tex")
    fixed_path = os.path.join(error_dir, fixed_name)
    with open(fixed_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Fixed saved: {fixed_name}")

    # 重新渲染图像
    out_image = fixed_path.replace(".tex", ".png")
    success_log = os.path.join(error_dir, "success_tables.txt")
    fail_log = os.path.join(error_dir, "failed_tables.txt")
    try:
        save_latex_as_image(content, outname=out_image.replace(".png", ""))
        print(f"Rendered image: {out_image}\n")
        # 记录渲染成功
        if os.path.exists(out_image):
            with open(success_log, "a") as f:
                f.write(f"{fixed_name}\n")
    except Exception as e:
        print(f"Failed to render {fixed_name}: {e}\n")
        # 记录渲染失败
        with open(fail_log, "a") as f:
            f.write(f"{fixed_name}: {e}\n")