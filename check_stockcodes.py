#!/usr/bin/env python3
"""Detailed stock code consistency check - v2."""
import os
import re
import glob

REPORTS_DIR = "/data/data/com.termux/files/home/.hermes/hermes-agent/report-portal/reports"
html_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.html")))

print(f"{'File':25s} {'Title':25s} {'JS Code':10s} {'s0 Code':10s} {'Footer Code':12s} {'Status'}")
print("=" * 95)

for f in html_files:
    basename = os.path.basename(f)
    content = open(f, 'r', encoding='utf-8').read()
    
    # Title
    title_match = re.search(r'<title>(.*?)</title>', content)
    title_text = title_match.group(1).replace('· 完整投资研究报告', '') if title_match else "N/A"
    title_text = title_text.strip()
    
    # JS stockCode
    js_match = re.search(r"stockCode\s*=\s*'(\d{4,6})'", content)
    js_code = js_match.group(1) if js_match else "N/A"
    
    # s0 h1 span
    s0_match = re.search(r'<h1[^>]*>.*?<span[^>]*>(\d{4,6})</span>', content, re.DOTALL)
    s0_code = s0_match.group(1) if s0_match else "N/A"
    
    # Footer
    footer_match = re.search(r'<div class="footer">.*?(\d{5,6})\.(SH|SZ)', content, re.DOTALL)
    footer_code = footer_match.group(1) if footer_match else "N/A"
    
    # Check consistency
    file_stem = basename.replace('.html', '')
    is_code_file = bool(re.match(r'^\d{5,6}$', file_stem))
    
    status = "✅ OK"
    codes_present = [c for c in [js_code, s0_code, footer_code] if c != "N/A"]
    
    if len(set(codes_present)) != 1:
        status = "❌ INCONSISTENT"
    elif is_code_file and file_stem != codes_present[0]:
        status = f"❌ MISMATCH (file={file_stem})"
    
    print(f"{basename:25s} {title_text:25s} {js_code:10s} {s0_code:10s} {footer_code:12s} {status}")
