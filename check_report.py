#!/usr/bin/env python3
"""Check PE template remnants and stock code consistency across all 37 reports."""
import os
import re
import glob

REPORTS_DIR = "/data/data/com.termux/files/home/.hermes/hermes-agent/report-portal/reports"
html_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.html")))

print(f"Total files: {len(html_files)}")
print("=" * 80)

# ===== PART 1: PE对比表残留 =====
print("\n\n===== PART 1: PE对比表残留 =====")
print("=" * 80)

# Check for battery industry stock names
battery_names = ['德赛电池', '珠海冠宇', '宁德时代']
for name in battery_names:
    print(f"\n--- Searching for: {name} ---")
    for f in html_files:
        basename = os.path.basename(f)
        content = open(f, 'r', encoding='utf-8').read()
        if name in content:
            # Find context
            for i, line in enumerate(content.split('\n'), 1):
                if name in line:
                    line_stripped = line.strip()[:120]
                    print(f"  {basename}:L{i} | {line_stripped}")

# Check for old-style PE values
print("\n\n--- PE Values with '×' (multiplication sign) in PE对比表 context ---")
for f in html_files:
    basename = os.path.basename(f)
    content = open(f, 'r', encoding='utf-8').read()
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'PE对比' in line or 'h3' in line.lower() and 'pe' in line.lower():
            # Check the next few lines for ×
            for j in range(i, min(i+10, len(lines)+1)):
                if '×' in lines[j-1] and re.search(r'\d+×', lines[j-1]):
                    print(f"  {basename}:L{j} | {lines[j-1].strip()[:120]}")
                    break

# ===== PART 2: 股票代码一致性 =====
print("\n\n===== PART 2: 股票代码一致性 =====")
print("=" * 80)

for f in html_files:
    basename = os.path.basename(f)  # e.g., "000063.html"
    content = open(f, 'r', encoding='utf-8').read()
    lines = content.split('\n')
    
    # Extract stock code from various locations
    title_name = ""
    stockcode_js = ""
    stockcode_s0 = ""
    stockcode_footer = ""
    
    # 1. <title> tag
    title_match = re.search(r'<title>(.*?)</title>', content)
    if title_match:
        title_text = title_match.group(1)
        # Try to find stock code in title
        code_in_title = re.search(r'(\d{5,6})', title_text)
        if code_in_title:
            title_code = code_in_title.group(1)
        else:
            title_code = title_text  # company name only
    
    # 2. K线JS - stockCode = '...'
    js_match = re.search(r"stockCode\s*=\s*'(\d{4,6})'", content)
    if js_match:
        stockcode_js = js_match.group(1)
    
    # 3. s0评分环区域 - h1 span
    s0_match = re.search(r'id="s0".*?<h1[^>]*>.*?<span[^>]*>(\d{4,6})</span>', content, re.DOTALL)
    if s0_match:
        stockcode_s0 = s0_match.group(1)
    
    # 4. footer
    footer_match = re.search(r'<div class="footer">.*?(\d{5,6})\.', content, re.DOTALL)
    if footer_match:
        stockcode_footer = footer_match.group(1)
    
    # Determine expected code for code-named files
    file_stem = basename.replace('.html', '')
    is_code_file = bool(re.match(r'^\d{5,6}$', file_stem))
    
    # Check consistency
    issues = []
    
    if is_code_file:
        if stockcode_js and stockcode_js != file_stem:
            issues.append(f"JS stockCode '{stockcode_js}' != filename '{file_stem}'")
        if stockcode_s0 and stockcode_s0 != file_stem:
            issues.append(f"s0评分环 code '{stockcode_s0}' != filename '{file_stem}'")
        if stockcode_footer and stockcode_footer != file_stem:
            issues.append(f"Footer code '{stockcode_footer}' != filename '{file_stem}'")
    
    # Internal consistency
    codes = [c for c in [stockcode_js, stockcode_s0, stockcode_footer] if c]
    if len(set(codes)) > 1:
        issues.append(f"Internal inconsistency: JS={stockcode_js}, s0={stockcode_s0}, footer={stockcode_footer}")
    
    if issues:
        print(f"\n⚠️  {basename}")
        for iss in issues:
            print(f"   {iss}")
        print(f"   JS={stockcode_js}, s0={stockcode_s0}, footer={stockcode_footer}")

print("\n\n===== DONE =====")
