#!/usr/bin/env python3
"""Fetch market cap data for a stock and generate 4 period JSON files.

Usage: python3 fetch_kline.py <stock_code>
  stock_code: e.g. sz000858 for Wuliangye (Sina format)

Output: kline/{stockCode}_day.json, _week.json, _month.json, _year.json
"""
import json, os, sys, requests, re
from datetime import datetime, timedelta
from collections import OrderedDict

SINA_URL = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
TENCENT_URL = "https://qt.gtimg.cn/q="

def fetch_daily_kline(stock_code):
    """Fetch all daily K-line data from Sina."""
    params = {"symbol": stock_code, "scale": "240", "ma": "no", "datalen": "8000"}
    resp = requests.get(SINA_URL, params=params, timeout=20)
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError(f"Unexpected response: {data}")
    print(f"  K-line data: {len(data)} trading days")
    if data:
        print(f"  Range: {data[0]['day']} ~ {data[-1]['day']}")
    return data

def fetch_total_shares(stock_code):
    """Fetch total shares from Tencent. stock_code in Sina format (sz000858)."""
    # Convert sz000858 -> sz000858 (Tencent uses same prefix format)
    resp = requests.get(TENCENT_URL + stock_code, timeout=10)
    text = resp.text
    # Parse the response format: v_sz000858="...~...~...~total_shares~..."
    # Total shares are typically field index 45 or 46 depending on exchange
    match = re.search(r'~([\d.]+)~总股本', text)
    if match:
        return float(match.group(1))
    # Fallback: try to extract from raw fields
    fields = text.split('~')
    for i, f in enumerate(fields):
        if '总股本' in f:
            return float(fields[i-1]) if i > 0 else 0
    # Last resort: look for a large number that could be total shares
    for f in fields:
        try:
            v = float(f)
            if v > 1e8 and v < 1e12:
                return v
        except:
            pass
    return 0

def calc_market_cap(kline_data, total_shares):
    """Calculate market cap for each day: close * total_shares / 1e8 -> 亿元."""
    results = []
    for item in kline_data:
        close = float(item.get('close', 0))
        day = item.get('day', '')
        if close and day:
            mcap = round(close * total_shares / 1e8, 2)
            results.append({"time": day, "value": mcap})
    return results

def get_week_start(date_str):
    """Get Monday of the week for a given date string YYYY-MM-DD."""
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
        grouped[key] = item  # Last value wins (most recent in period)
    
    result = list(grouped.values())
    # Sort by time
    result.sort(key=lambda x: x['time'])
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_kline.py <stock_code>")
        print("Example: python3 fetch_kline.py sz000858")
        sys.exit(1)
    
    stock_code = sys.argv[1]
    # Strip prefix for file naming
    code_clean = stock_code.lower().replace('sh', '').replace('sz', '')
    
    # Output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    kline_dir = os.path.join(repo_dir, 'kline')
    os.makedirs(kline_dir, exist_ok=True)
    
    print(f"Fetching data for {stock_code}...")
    
    # Step 1: Fetch daily K-line
    print("Step 1: Fetching daily K-line from Sina...")
    kline = fetch_daily_kline(stock_code)
    
    # Step 2: Fetch total shares
    print("Step 2: Fetching total shares from Tencent...")
    total_shares = fetch_total_shares(stock_code)
    print(f"  Total shares: {total_shares:.2f}")
    
    if total_shares == 0:
        print("ERROR: Could not determine total shares. Check stock code.")
        sys.exit(1)
    
    # Step 3: Calculate daily market cap
    print("Step 3: Calculating market cap...")
    daily_data = calc_market_cap(kline, total_shares)
    print(f"  Daily data points: {len(daily_data)}")
    if daily_data:
        print(f"  Min mcap: {min(d['value'] for d in daily_data):.2f}亿")
        print(f"  Max mcap: {max(d['value'] for d in daily_data):.2f}亿")
    
    # Step 4: Generate 4 period files
    print("Step 4: Generating period files...")
    
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
    print(f"Stock: {stock_code}, Total Shares: {total_shares:.2f}")

if __name__ == '__main__':
    main()
