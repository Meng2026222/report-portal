#!/usr/bin/env python3
"""Weekly update script: fetch market cap data for ALL stocks and push to GitHub Pages.
Called by Hermes cron job every Friday at 17:00.
"""
import subprocess, sys, os

REPO_DIR = '/data/data/com.termux/files/home/.hermes/hermes-agent/report-portal'
FETCH_SCRIPT = os.path.join(REPO_DIR, 'scripts', 'fetch_kline.py')

STOCKS = [
    # A-share
    'sh600519', 'sz000858', 'sh600887', 'sh603288', 'sz300750',
    'sz002594', 'sh601127', 'sh601318', 'sh600036', 'sz300308',
    'sz002475', 'sz002415', 'sh600660', 'sh600276', 'sz300760',
    # HK stocks (prefix hk)
    'hk02015',  # 理想汽车-W
]

def run(cmd, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or REPO_DIR, timeout=120)
    if result.returncode != 0:
        print(f"ERROR: {' '.join(cmd)}")
        print(result.stderr[:200])
        return False
    print(result.stdout.strip())
    return True

def main():
    print("=" * 40)
    print(f"批量市值数据更新 ({len(STOCKS)}家企业)")
    print("=" * 40)

    # Step 1: Fetch all stocks
    for stock in STOCKS:
        print(f"\n[{stock}]")
        result = subprocess.run(
            [sys.executable, FETCH_SCRIPT, stock],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[:100]}")
        else:
            for line in result.stdout.strip().split('\n'):
                if '✅' in line:
                    print(f"  {line.strip()}")

    # Step 2: Check if anything changed
    print("\n检查数据是否有更新...")
    status = subprocess.run(
        ['git', 'status', '--porcelain', 'kline/'],
        capture_output=True, text=True, cwd=REPO_DIR, timeout=10
    )
    if not status.stdout.strip():
        print("数据无变化，跳过提交。")
        return

    # Step 3: Commit and push
    print("提交并推送到 GitHub Pages...")
    if not run(['git', 'add', 'kline/']):
        return
    if not run(['git', 'commit', '-m', 'chore: update kline data']):
        return
    if not run(['git', 'push']):
        return

    print("\n✅ 全部更新完成！")

if __name__ == '__main__':
    main()
