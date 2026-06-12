#!/usr/bin/env python3
"""Fetch market cap data for a stock and generate 4 period JSON files.

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

SINA_URL = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
EASTMONEY_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q="


def is_hk_stock(stock_code):
    """Detect if it's a HK stock (hk prefix or 5-digit HK code)."""
    return stock_code.lower().startswith('hk')


def get_eastmoney_secid(stock_code):
    """Get East Money secid for A-share. sh=1, sz=0."""
    code = stock_code.lower()
    if code.startswith('sh'):
        return f"1.{code.replace('sh', '')}"
    elif code.startswith('sz'):
        return f"0.{code.replace('sz', '')}"
    return None


def fetch_daily_kline_a(stock_code):
    """Fetch daily K-line for A-share from East Money (前复权 fqt=1)."""
    secid = get_eastmoney_secid(stock_code)
    if not secid:
        raise ValueError(f"Cannot determine secid for {stock_code}")
    params = {
        "secid": secid,
        "fields1": "f1",
        "fields2": "f51,f52,f53,f54,f55,f56,f57",
        "klt": "101",
        "fqt": "1",          # 前复权 (forward-adjusted)
        "end": "20500101",
        "lmt": "10000",
    }
    resp = requests.get(EASTMONEY_URL, params=params, timeout=20)
    data = resp.json()
    kd = data.get("data")
    if not kd or "klines" not in kd:
        raise ValueError(f"Unexpected A-share EastMoney response: {data}")
    klines = kd["klines"]
    result = []
    for line in klines:
        parts = line.split(",")
        if len(parts) >= 3:
            result.append({"day": parts[0], "close": float(parts[2])})
    print(f"  K-line data: {len(result)} trading days")
    if result:
        print(f"  Range: {result[0]['day']} ~ {result[-1]['day']}")
        print(f"  Data source: East Money (前复权 fqt=1)")
    return result


def fetch_daily_kline_hk(stock_code):
    """Fetch daily K-line for HK stock from East Money API (secid=128.xxxx)."""
    code_clean = stock_code.lower().replace('hk', '')
    # East Money market code 128 = HK stocks
    params = {
        "secid": f"128.{code_clean}",
        "fields1": "f1",
        "fields2": "f51,f52,f53,f54,f55,f56,f57",
        "klt": "101",       # daily
        "fqt": "1",         # forward-adjusted
        "end": "20500101",
        "lmt": "8000",
    }
    resp = requests.get(EASTMONEY_URL, params=params, timeout=20)
    data = resp.json()
    kd = data.get("data")
    if not kd or "klines" not in kd:
        raise ValueError(f"Unexpected HK EastMoney response: {data}")
    klines = kd["klines"]
    # Format: date,open,close,high,low,volume,amount
    result = []
    for line in klines:
        parts = line.split(",")
        if len(parts) >= 3:
            result.append({
                "day": parts[0],
                "close": float(parts[2]),
            })
    print(f"  K-line data: {len(result)} trading days")
    if result:
        print(f"  Range: {result[0]['day']} ~ {result[-1]['day']}")
    return result


def fetch_total_shares(stock_code):
    """Fetch total shares from Tencent quote API."""
    resp = requests.get(TENCENT_QUOTE_URL + stock_code, timeout=10)
    text = resp.text
    fields = text.split('~')

    if is_hk_stock(stock_code):
        # HK stock: field 69 = total shares (in 股)
        # Fallback: calculate from field 45 (总市值 亿) / current price
        try:
            total_shares = float(fields[69]) if len(fields) > 69 and fields[69] else 0
            if total_shares > 0:
                print(f"  Total shares from field 69: {total_shares:.0f}")
                return total_shares
        except (ValueError, IndexError):
            pass
        # Fallback: field 45 (总市值 亿) / field 3 (current price) * 1e8
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
        # A-share: search for 总股本
        match = re.search(r'~([\d.]+)~总股本', text)
        if match:
            return float(match.group(1))
        # Fallback parse
        for i, f in enumerate(fields):
            if '总股本' in f:
                return float(fields[i - 1]) if i > 0 else 0
        # Last resort
        for f in fields:
            try:
                v = float(f)
                if v > 1e8 and v < 1e12:
                    return v
            except:
                pass
        return 0


def calc_market_cap(kline_data, total_shares):
    """Calculate market cap: close * total_shares / 1e8 -> 亿元.
    前复权(fqt=1)价格可能因累计分红使早期数据为负，下限保护cap为0。"""
    results = []
    for item in kline_data:
        close = float(item.get('close', 0))
        day = item.get('day', '')
        if close and day:
            mcap = round(close * total_shares / 1e8, 2)
            if mcap < 0:
                mcap = 0  # 前复权导致的价格为负，cap为0
            results.append({"time": day, "value": mcap})
    return results


def get_week_start(date_str):
    """Get Monday of the week for YYYY-MM-DD."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


def aggregate_by_period(data, period='week'):
    """Aggregate daily data to week/month/year. Take last entry of each period."""
    grouped = OrderedDict()
    for item in data:
        d = item['time']
        if period == 'week':
            key = get_week_start(d)
        elif period == 'month':
            key = d[:7]  # YYYY-MM
        elif period == 'year':
            key = d[:4]  # YYYY
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

    stock_code = sys.argv[1]
    code_lower = stock_code.lower()

    # Strip prefix for file naming
    if is_hk_stock(stock_code):
        code_clean = code_lower.replace('hk', '')
        data_source = "HK"
    else:
        code_clean = code_lower.replace('sh', '').replace('sz', '')
        data_source = "A-share"

    # Output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    kline_dir = os.path.join(repo_dir, 'kline')
    os.makedirs(kline_dir, exist_ok=True)

    print(f"Fetching {data_source} data for {stock_code}...\n")

    # Step 1: Fetch daily K-line
    print("Step 1: Fetching daily K-line...")
    if is_hk_stock(stock_code):
        kline = fetch_daily_kline_hk(stock_code)
    else:
        kline = fetch_daily_kline_a(stock_code)

    # Step 2: Fetch total shares
    print("\nStep 2: Fetching total shares...")
    total_shares = fetch_total_shares(stock_code)
    print(f"  Total shares: {total_shares:.2f}")

    if total_shares == 0:
        print("ERROR: Could not determine total shares. Check stock code.")
        sys.exit(1)
    total_shares_yi = total_shares / 1e8
    print(f"  = {total_shares_yi:.2f}亿股")

    # Step 3: Calculate daily market cap
    print("\nStep 3: Calculating market cap...")
    daily_data = calc_market_cap(kline, total_shares)
    print(f"  Daily data points: {len(daily_data)}")
    if daily_data:
        print(f"  Min mcap: {min(d['value'] for d in daily_data):.2f}亿")
        print(f"  Max mcap: {max(d['value'] for d in daily_data):.2f}亿")
        print(f"  Current: {daily_data[-1]['value']:.2f}亿 ({daily_data[-1]['time']})")

    # Step 4: Generate 4 period files
    print("\nStep 4: Generating period files...")
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
    print(f"Stock: {stock_code} ({data_source}), Total Shares: {total_shares_yi:.2f}亿")


if __name__ == '__main__':
    main()
