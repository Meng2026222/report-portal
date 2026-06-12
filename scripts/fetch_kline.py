#!/usr/bin/env python3
"""Fetch market cap data for a stock and generate 4 period JSON files.

Uses 不复权 (raw) prices + stock-split detection to compute TRUE historical market cap,
avoiding the negative-price artifact from 前复权 dividend adjustment.

Usage: python3 fetch_kline.py <stock_code>
  stock_code examples:
    sz000858    — A-share (Shenzhen)
    sh600085    — A-share (Shanghai)
    hk02015     — HK stock (Hong Kong)

Output: kline/{stockCode}_day.json, _week.json, _month.json, _year.json
"""
import json, os, sys, re
from datetime import datetime, timedelta
from collections import OrderedDict
import requests

EASTMONEY_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q="


def is_hk_stock(stock_code):
    return stock_code.lower().startswith('hk')


def get_eastmoney_secid(stock_code):
    """Get East Money secid. sh=1, sz=0, hk=128."""
    code = stock_code.lower()
    if code.startswith('hk'):
        return f"128.{code.replace('hk', '')}"
    elif code.startswith('sh'):
        return f"1.{code.replace('sh', '')}"
    elif code.startswith('sz'):
        return f"0.{code.replace('sz', '')}"
    return None


def fetch_kline_eastmoney(secid, fqt):
    """Fetch daily K-line from East Money with given 复权 type.
    fqt=0: 不复权, fqt=1: 前复权, fqt=2: 后复权
    """
    params = {
        "secid": secid,
        "fields1": "f1",
        "fields2": "f51,f52,f53,f54,f55,f56,f57",
        "klt": "101",
        "fqt": str(fqt),
        "end": "20500101",
        "lmt": "10000",
    }
    resp = requests.get(EASTMONEY_URL, params=params, timeout=20)
    data = resp.json()
    kd = data.get("data")
    if not kd or "klines" not in kd:
        return None
    klines = kd["klines"]
    result = []
    for line in klines:
        parts = line.split(",")
        if len(parts) >= 3:
            result.append({"day": parts[0], "close": float(parts[2])})
    return result


def fetch_total_shares(stock_code):
    """Fetch total shares from Tencent quote API."""
    resp = requests.get(TENCENT_QUOTE_URL + stock_code, timeout=10)
    text = resp.text
    fields = text.split('~')

    if is_hk_stock(stock_code):
        try:
            total_shares = float(fields[69]) if len(fields) > 69 and fields[69] else 0
            if total_shares > 0:
                print(f"  Total shares from field 69: {total_shares:.0f}")
                return total_shares
        except (ValueError, IndexError):
            pass
        try:
            total_mcap = float(fields[45])
            current_price = float(fields[3])
            if total_mcap > 0 and current_price > 0:
                shares = total_mcap * 1e8 / current_price
                print(f"  Total shares calculated: {shares:.0f}")
                return shares
        except (ValueError, IndexError):
            pass
        return 0
    else:
        match = re.search(r'~([\d.]+)~总股本', text)
        if match:
            return float(match.group(1))
        for i, f in enumerate(fields):
            if '总股本' in f:
                return float(fields[i - 1]) if i > 0 else 0
        for f in fields:
            try:
                v = float(f)
                if v > 1e8 and v < 1e12:
                    return v
            except:
                pass
        return 0


def detect_splits(raw, adj):
    """Detect stock splits by comparing 不复权 and 前复权 daily data.
    
    Only detects SIGNIFICANT splits (ratio >= 1.5), to avoid noise from
    normal price movements and small bonus issues (10送1 etc).
    
    A stock split causes a sharp drop in 不复权 price but NOT in 前复权 price
    (because 前复权 adjusts for splits).
    
    Returns: list of (index, split_ratio) sorted from newest to oldest.
    """
    MIN_MULT = 1.5  # Minimum split ratio to detect (10送5 or larger)
    splits = []
    for i in range(1, len(raw)):
        raw_prev = raw[i-1]['close']
        raw_curr = raw[i]['close']
        adj_prev = adj[i-1]['close']
        adj_curr = adj[i]['close']
        
        if raw_prev <= 0 or adj_prev <= 0:
            continue
        
        raw_ratio = raw_curr / raw_prev  # < 1 if price dropped
        adj_ratio = adj_curr / adj_prev
        
        # Split detection: 不复权 drops sharply but 前复权 doesn't
        # raw_ratio < 1/MIN_MULT means price dropped by more than 1 - 1/MIN_MULT
        if raw_ratio < 1.0 / MIN_MULT and adj_ratio > 0.95:
            # The split ratio = round(raw_prev / raw_curr)
            mult = round(raw_prev / raw_curr)
            if 2 <= mult <= 30:
                splits.append((i, mult))
    
    # Sort newest first
    splits.sort(key=lambda x: -x[0])
    return splits


def compute_shares(current_shares, splits, total_points):
    """Build per-day share count array by unwinding splits backwards.
    
    Starting from current shares, divide by split_ratio at each split going back.
    Returns a list of share counts, one per day, from oldest to newest.
    """
    shares = [0] * total_points
    split_idx = 0
    cumulative = current_shares
    
    for i in range(total_points - 1, -1, -1):
        # Check if this index has a split (going backwards, we adjust shares BEFORE the split)
        while split_idx < len(splits) and splits[split_idx][0] >= i:
            # Going backwards: the split just happened, so before it shares were smaller
            cumulative = cumulative / splits[split_idx][1]
            split_idx += 1
        shares[i] = cumulative
    
    return shares


def calc_market_cap(stock_code):
    """Main function: calculate TRUE historical market cap using 不复权 + detected splits."""
    secid = get_eastmoney_secid(stock_code)
    if not secid:
        raise ValueError(f"Cannot determine secid for {stock_code}")

    code_clean = stock_code.lower().replace('sh', '').replace('sz', '').replace('hk', '')
    data_source = "HK" if is_hk_stock(stock_code) else "A-share"
    
    print(f"Fetching {data_source} data for {stock_code}...\n")

    # Step 1: Fetch both 前复权 and 不复权
    print("Step 1: Fetching K-line data...")
    adj = fetch_kline_eastmoney(secid, 1)  # 前复权
    raw = fetch_kline_eastmoney(secid, 0)  # 不复权
    
    if not adj or not raw:
        raise ValueError("Failed to fetch K-line data")
    
    print(f"  前复权: {len(adj)} trading days ({adj[0]['day']} ~ {adj[-1]['day']})")
    print(f"  不复权: {len(raw)} trading days ({raw[0]['day']} ~ {raw[-1]['day']})")
    
    # Align both datasets to same date range (use intersection)
    # Build dicts by date for alignment
    adj_by_day = {d['day']: d['close'] for d in adj}
    raw_by_day = {d['day']: d['close'] for d in raw}
    common_days = sorted(set(adj_by_day.keys()) & set(raw_by_day.keys()))
    
    aligned_adj = [{"day": d, "close": adj_by_day[d]} for d in common_days]
    aligned_raw = [{"day": d, "close": raw_by_day[d]} for d in common_days]
    
    print(f"  Aligned: {len(common_days)} common trading days")
    
    # Step 2: Fetch total shares
    print("\nStep 2: Fetching total shares...")
    total_shares = fetch_total_shares(stock_code)
    print(f"  Total shares: {total_shares:.2f}")
    if total_shares == 0:
        print("ERROR: Could not determine total shares.")
        sys.exit(1)
    total_shares_yi = total_shares / 1e8
    print(f"  = {total_shares_yi:.2f}亿股")

    # Step 3: Detect stock splits
    print("\nStep 3: Detecting stock splits...")
    splits = detect_splits(aligned_raw, aligned_adj)
    if splits:
        # Convert from aligned index to actual dates
        split_dates = [(aligned_raw[idx]['day'], ratio) for idx, ratio in splits]
        for dt, ratio in split_dates:
            print(f"  ✅ {dt}: 拆股 1:{ratio}")
    else:
        print("  No stock splits detected")
    
    # Step 4: Build share count history
    print("\nStep 4: Computing historical share counts...")
    share_counts = compute_shares(total_shares, splits, len(aligned_raw))
    print(f"  Share count range: {share_counts[0]/1e8:.2f}亿 ~ {share_counts[-1]/1e8:.2f}亿")

    # Step 5: Calculate market cap = 不复权_price × shares_at_that_time
    print("\nStep 5: Calculating TRUE market cap...")
    daily_data = []
    for i, item in enumerate(aligned_raw):
        mcap = round(item['close'] * share_counts[i] / 1e8, 2)
        if mcap < 0:
            mcap = 0  # Safety cap (shouldn't happen with 不复权)
        daily_data.append({"time": item['day'], "value": mcap})
    
    print(f"  Daily data points: {len(daily_data)}")
    if daily_data:
        vals = [d['value'] for d in daily_data]
        print(f"  Min mcap: {min(vals):.2f}亿")
        print(f"  Max mcap: {max(vals):.2f}亿")
        print(f"  Current: {daily_data[-1]['value']:.2f}亿 ({daily_data[-1]['time']})")

    # Step 6: Save period files
    print("\nStep 6: Generating period files...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    kline_dir = os.path.join(repo_dir, 'kline')
    os.makedirs(kline_dir, exist_ok=True)

    periods = {
        'day': daily_data,
        'week': aggregate_by_period(daily_data, 'week'),
        'month': aggregate_by_period(daily_data, 'month'),
        'year': aggregate_by_period(daily_data, 'year'),
    }
    for period_name, period_data in periods.items():
        filename = f"{code_clean}_{period_name}.json"
        filepath = os.path.join(kline_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(period_data, f, ensure_ascii=False)
        print(f"  ✅ {filename}: {len(period_data)} data points")

    print(f"\nAll files saved to: {kline_dir}/")
    print(f"Stock: {stock_code} ({data_source}), Current Shares: {total_shares_yi:.2f}亿")


def get_week_start(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


def aggregate_by_period(data, period='week'):
    grouped = OrderedDict()
    for item in data:
        d = item['time']
        if period == 'week':
            key = get_week_start(d)
        elif period == 'month':
            key = d[:7]
        elif period == 'year':
            key = d[:4]
        else:
            key = d
        grouped[key] = item
    result = list(grouped.values())
    result.sort(key=lambda x: x['time'])
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_kline.py <stock_code>")
        print("Examples:")
        print("  python3 fetch_kline.py sz000858   # A-share (Shenzhen)")
        print("  python3 fetch_kline.py sh600085   # A-share (Shanghai)")
        print("  python3 fetch_kline.py hk02015    # HK stock")
        sys.exit(1)
    calc_market_cap(sys.argv[1])


if __name__ == '__main__':
    main()
