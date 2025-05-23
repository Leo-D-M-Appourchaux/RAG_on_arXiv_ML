import re
#主要想实现对表格中数据的增删改

__all__ = [
    "modify_numeric_values",
    "drop_table_column",
    "drop_table_row",
    "insert_row",
    "insert_empty_row_auto",
    "insert_column",
    "update_tabular_column_format",
    "clean_latex_string",
    "get_table_col_count",
    "finalize_latex_structure",
]

# 在对 original_latex 进行任何操作前，先清理字符串
# 例如:
# original_latex = clean_latex_string(original_latex)

# 新增：清理 LaTeX 字符串中的非法控制字符
def clean_latex_string(text):
    """
    清理 LaTeX 字符串中的非法控制字符（如 ASCII < 32，保留 \n 和 \t）
    """
    return ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\t')

#替换表格中的数值字符串
def modify_numeric_values(latex_str, old_val, new_val):
    """
    替换 LaTeX 表格中的某个数值
    """
    return latex_str.replace(old_val, new_val)

#删除指定的列（第 col_index 列，从 0 开始）
def drop_table_column(latex_str, col_index=1):
    """
    删除表格中的第 col_index 列（从 0 开始计数）
    """
    new_lines = []
    for line in latex_str.split("\n"):
        if '&' in line:
            parts = [p.strip() for p in line.split('&')]
            if 0 <= col_index < len(parts):
                parts.pop(col_index)
                line = ' & '.join(parts)
        new_lines.append(line)
    return '\n'.join(new_lines)

#删除第 row_index 行的数据（排除表头），用于行级内容裁剪
def drop_table_row(latex_str, row_index=0):
    """
    删除第 row_index 行（从 0 开始计数，不包括表头）
    """
    new_lines = []
    data_row_count = 0
    for line in latex_str.split("\n"):
        if '&' in line:
            if data_row_count == row_index:
                data_row_count += 1
                continue
            data_row_count += 1
        new_lines.append(line)
    return '\n'.join(new_lines)

#手动插入一行，通常在 \bottomrule 或指定位置前插入
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
    在每一行中插入一列
    """
    new_lines = []
    for line in latex_str.split("\n"):
        if '&' in line:
            parts = [p.strip() for p in line.split('&')]
            if 0 <= col_index <= len(parts): 
                parts.insert(col_index, default_value)
                line = ' & '.join(parts)
        new_lines.append(line)
    return '\n'.join(new_lines)

def modify_column_spec(latex_line, addition="p{3cm}|"):
    brace_count = 0
    first_done = False
    start_idx = None
    end_idx = None

    for i, char in enumerate(latex_line):
        if char == '{':
            brace_count += 1
            if brace_count == 1 and not first_done:
                first_done = True
            elif brace_count == 1 and first_done and start_idx is None:
                start_idx = i + 1  # content starts after this
        elif char == '}':
            if brace_count == 1 and start_idx is not None and end_idx is None:
                end_idx = i  # content ends before this
                break
            brace_count -= 1

    if start_idx is not None and end_idx is not None:
        # Get original column spec
        colspec = latex_line[start_idx:end_idx]
        new_colspec = colspec + addition
        return latex_line[:start_idx] + new_colspec + latex_line[end_idx:]
    else:
        return latex_line  # unchanged if not found


def add_column_to_outermost_tabular(latex_str, new_cell_value=" NEW "):
    lines = latex_str.splitlines()
    new_lines = []
    nest = 0
    inside_outer_tabular = False

    for line in lines:
        stripped = line.strip()

        match = re.match(r'(\\begin\{tabular\})\{([^}]*)\}', stripped)
        if match:
            nest += 1
            if nest == 1:
                inside_outer_tabular = True
                original_start, colspec = match.groups()
                line = modify_column_spec(line, addition="p{3cm}|")

        elif r'\end{tabular}' in stripped:
            if nest == 1:
                inside_outer_tabular = False
            nest -= 1
       

        # Modify only inside the outermost tabular
        if inside_outer_tabular:
            # Patch multicolumn if found
            if r'\multicolumn{' in line:
                line = re.sub(r'\\multicolumn\{(\d+)\}', lambda m: f'\\multicolumn{{{int(m.group(1)) + 1}}}', line)
            
            if r'\cline{' in line:
                line = re.sub(r'\\cline\{(\d+)-(\d+)\}', lambda m: fr'\cline{{{m.group(1)}-{int(m.group(2))+1}}}', line)

            # Add a new cell to data rows
            if '&' in line and r'\\' in line:
                parts = line.split('&')
                parts.insert(-1, new_cell_value)
                line = ' & '.join(parts)

        new_lines.append(line)

    return '\n'.join(new_lines)

def update_tabular_column_format(latex_str, new_col_count):

    col_def = '|'.join([f'p{{3cm}}' for _ in range(new_col_count)])
    new_tabular = '\\begin{tabular}{|' + col_def + '|}'

    # 清理非可见字符（比如 \x08）
    new_tabular = ''.join(ch for ch in new_tabular if ch >= ' ' or ch in '\n\t')
    
    print("new_tabular:", repr(new_tabular))  # 确认是否被修复 调试是否出现非法字符

    return re.sub(r'\\begin{tabular}{[^}]+}', new_tabular, latex_str, count=1)


def get_table_col_count(latex_str):
    """
    尝试自动计算表格的列数（基于第一行带有 & 的数据）
    """
    for line in latex_str.split("\n"):
        if '&' in line and '\\' in line:
            return line.count('&') + 1
    return None

def finalize_latex_structure(latex_str):
    if not latex_str.strip().startswith("\\begin{table}"):
        latex_str = "\\begin{table}\n" + latex_str
    col_count = get_table_col_count(latex_str)
    if col_count is not None:
        latex_str = update_tabular_column_format(latex_str, col_count)
        latex_str = update_multicolumn_and_cline(latex_str, col_count)
    return latex_str

def update_multicolumn_and_cline(latex_str, new_col_count):
    latex_str = re.sub(r'\\multicolumn{(\d+)}', fr'\\multicolumn{{{new_col_count}}}', latex_str)
    latex_str = re.sub(r'\\cline{1-\d+}', fr'\\cline{{1-{new_col_count}}}', latex_str)
    return latex_str

def check_text(latex_str):
    print(latex_str.keys())
    return latex_str.keys()

'''
测试功能
if __name__ == "__main__":
    def test_pipeline():
        raw = r"""
        \begin{table}[H]
        \centering
        \scriptsize
        \begin{tabular}{|p{3cm}|p{3cm}|}
        \hline
        A & B \\
        \hline
        10 & 2 \\
        \hline
        \end{tabular}
        \end{table}
        """
        from pprint import pprint

        print("原始 LaTeX：")
        pprint(raw)

        # 清理
        cleaned = clean_latex_string(raw)

        # 替换值
        modified = modify_numeric_values(cleaned, old_val="10", new_val="99")

        # 插入列
        modified = insert_column(modified, col_index=1, default_value="NEW")

        # 删除列
        modified = drop_table_column(modified, col_index=2)

        # 插入行（自动）
        modified = insert_empty_row_auto(modified, default="EMPTY")

        # 删除第一数据行
        modified = drop_table_row(modified, row_index=0)

        # 最终更新结构
        modified = finalize_latex_structure(modified)

        print("\n 最终 LaTeX：")
        pprint(modified)

    test_pipeline()
    '''