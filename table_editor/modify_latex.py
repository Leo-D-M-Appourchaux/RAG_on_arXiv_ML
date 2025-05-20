import re
#主要想实现对表格中数据的增删改
def modify_numeric_values(latex_str, old_val, new_val):
    """
    修改 LaTeX 表格中的某个数值
    """
    return latex_str.replace(old_val, new_val)

def drop_table_column(latex_str, col_index):
    """
    删除表格中的第 col_index 列（从 0 开始计数）
    """
    new_lines = []
    for line in latex_str.split("\n"):
        if '&' in line:
            parts = line.split('&')
            # 加入越界判断
            if 0 <= col_index < len(parts):
                parts.pop(col_index)
            else:
                print(f"当前行列数为 {len(parts)}，无法删除第 {col_index} 列。")
                # 去掉多余空格
            parts = [p.strip() for p in parts]
            line = ' & '.join(parts)
        new_lines.append(line)
    updated = '\n'.join(new_lines)
    col_count = get_table_col_count(updated)
    if col_count is not None:
        updated = update_tabular_column_format(updated, col_count)
    return updated

def drop_table_row(latex_str, row_index):
    """
    删除第 row_index 行（从 0 开始计数，排除表头）
    """
    new_lines = []
    data_row_count = 0

    for line in latex_str.split("\n"):
        if '&' in line:
            # 遇到数据行
            if data_row_count == row_index:
                data_row_count += 1
                continue  # 跳过该行
            data_row_count += 1
        new_lines.append(line)
    return '\n'.join(new_lines)

def insert_row(latex_str, row_str, before="\\bottomrule"):
    """
    插入指定内容的一行（如 'X & Y & Z \\'），默认在 \\bottomrule 前。
    """
    return latex_str.replace(before, row_str + "\n" + before)

def insert_empty_row_auto(latex_str, before="\\bottomrule", default=""):
    """
    自动识别列数，插入一个空值行（如 '& & &'）。
    """
    match = re.search(r'\\begin{tabular}{([^}]+)}', latex_str)
    if not match:
        return latex_str
    col_spec = match.group(1)
    num_cols = len(col_spec)
    new_row = ' & '.join([default] * num_cols) + r' \\'
    return latex_str.replace(before, new_row + "\n" + before)

def insert_column(latex_str, col_index=1, default_value=""):
    """
    在每一行中插入一列，并尝试更新列格式
    """
    new_lines = []
    for line in latex_str.split("\n"):
        if '&' in line:
            parts = [p.strip() for p in line.split('&')]
            if 0 <= col_index <= len(parts):
                parts.insert(col_index, default_value)
                line = ' & '.join(parts)
        new_lines.append(line) 
    updated = '\n'.join(new_lines)
    # 重新计算列数并更新 tabular 格式
    col_count = get_table_col_count(updated)
    if col_count is not None:
        updated = update_tabular_column_format(updated, col_count)
        print("✅ 插入列后 LaTeX：", repr(updated))
    return updated

def get_table_col_count(latex_str):
    """
    从表格中自动识别列数（只找第一行带 & 和 \\ 的行）
    """
    for line in latex_str.split("\n"):
        if '&' in line and '\\' in line:
            return line.count('&') + 1
    return None

def insert_row_auto(latex_str, fill="NEW", before="\\bottomrule"):
    """
    自动判断列数，在 bottomrule 前插入一行填充数据
    """
    col_count = get_table_col_count(latex_str)
    if col_count is None:
        raise ValueError("无法自动识别表格列数，插入失败。")

    row = " & ".join([fill] * col_count) + r" \\"
    return latex_str.replace(before, row + "\n" + before)

import re

def update_tabular_column_format(latex_str, new_col_count):
    """
    根据新的列数更新 tabular 的列格式，只替换列定义部分
    """
    import re
    col_def = '|'.join([f'p{{3cm}}' for _ in range(new_col_count)])
    new_format = f'\\begin{{tabular}}{{|{col_def}|}}'
    print("✅ 正在替换 tabular 格式为：", repr(new_format))

    updated = re.sub(r'\\begin{tabular}\{[^}]+\}', new_format, latex_str, count=1)
    print("💡 格式更新后：", repr(updated))
    return updated

def finalize_latex_structure(latex_str):
    """
    自动识别列数并更新 tabular 格式（供保存前使用）
    """
    col_count = get_table_col_count(latex_str)
    if col_count is not None:
        print("🧩 正在调用 finalize 结构更新")
        return update_tabular_column_format(latex_str, col_count)
    return latex_str
__all__ = [
    "modify_numeric_values",
    "drop_table_column",
    "drop_table_row",
    "insert_row",
    "insert_empty_row_auto",
    "insert_column",
    "get_table_col_count",
    "insert_row_auto",
    "update_tabular_column_format",
    "finalize_latex_structure"
]
