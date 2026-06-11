// ===== 财报指标连连看 · 大题库 =====
// 每个级别10+个指标，每局随机抽4对，可玩性拉满

const MATCH_POOL = {
  初级: {
    desc: '基础财务指标',
    pairs: [
      { term: 'ROE<br><small>净资产收益率</small>', def: '净利润 ÷ 净资产<br>衡量股东每一块钱能赚回多少利润<br><span class="mhint">15%以上为优秀，茅台28%</span>' },
      { term: '毛利率<br><small>Gross Margin</small>', def: '(营收 − 营业成本) ÷ 营收<br>衡量产品溢价能力和行业地位<br><span class="mhint">茅台91%+，制造业一般20-30%</span>' },
      { term: '净利率<br><small>Net Margin</small>', def: '净利润 ÷ 营收<br>衡量公司最终的盈利水平<br><span class="mhint">中际旭创22.7%，越稳定越好</span>' },
      { term: '资产负债率<br><small>Debt Ratio</small>', def: '总负债 ÷ 总资产<br>衡量财务杠杆和偿债风险<br><span class="mhint">40-60%较健康，过高有风险</span>' },
      { term: '总资产收益率<br><small>ROA</small>', def: '净利润 ÷ 总资产<br>衡量公司所有资产（含负债）的赚钱效率<br><span class="mhint">ROA > 5% 算不错</span>' },
      { term: '营业利润率<br><small>Operating Margin</small>', def: '营业利润 ÷ 营收<br>衡量主营业务的真实盈利能力<br><span class="mhint">排除了非经常性损益的影响</span>' },
      { term: '流动比率<br><small>Current Ratio</small>', def: '流动资产 ÷ 流动负债<br>衡量短期偿债能力<br><span class="mhint">大于2较安全，小于1需警惕</span>' },
      { term: '速动比率<br><small>Quick Ratio</small>', def: '(流动资产 − 存货) ÷ 流动负债<br>更保守的短期偿债指标<br><span class="mhint">大于1较安全</span>' },
      { term: '营收增长率<br><small>Revenue Growth</small>', def: '(本期营收 − 上期营收) ÷ 上期营收<br>衡量公司扩张速度<br><span class="mhint">要看是否可持续，警惕一次性暴增</span>' },
      { term: '净利润增长率<br><small>Net Profit Growth</small>', def: '(本期净利润 − 上期净利润) ÷ 上期净利润<br>衡量盈利能力提升速度<br><span class="mhint">长期稳定增长=好信号</span>' },
    ]
  },
  中级: {
    desc: '估值与效率指标',
    pairs: [
      { term: 'PE<br><small>市盈率</small>', def: '股价 ÷ 每股收益 (EPS)<br>市场愿意为每一块钱利润支付的价格<br><span class="mhint">茅台20.7x，中际旭创21.5x</span>' },
      { term: 'PB<br><small>市净率</small>', def: '股价 ÷ 每股净资产<br>市场对公司资产的溢价程度<br><span class="mhint">>1有溢价，<1可能被低估</span>' },
      { term: '股息率<br><small>Dividend Yield</small>', def: '每股股息 ÷ 股价<br>持有股票的现金回报率<br><span class="mhint">茅台3.2%，长期稳定分红是好信号</span>' },
      { term: '资产周转率<br><small>Asset Turnover</small>', def: '营收 ÷ 总资产<br>每一块钱资产能产生多少营收<br><span class="mhint">越高运营效率越好，零售业通常较高</span>' },
      { term: '存货周转率<br><small>Inventory Turnover</small>', def: '营业成本 ÷ 平均存货<br>存货卖出去的速度<br><span class="mhint">越高越好，但过高可能说明缺货</span>' },
      { term: '应收账款周转率<br><small>Receivables Turnover</small>', def: '营收 ÷ 平均应收账款<br>收钱的速度<br><span class="mhint">越高说明回款能力强</span>' },
      { term: 'PS<br><small>市销率</small>', def: '市值 ÷ 营收<br>每块钱营收对应的市场定价<br><span class="mhint">适用于亏损公司估值，越低越好</span>' },
      { term: 'PEG<br><small>市盈增长比</small>', def: 'PE ÷ 盈利增长率<br>结合估值和增长的指标<br><span class="mhint">PEG < 1 可能被低估</span>' },
      { term: '每股净资产<br><small>BVPS</small>', def: '净资产 ÷ 总股本<br>每一股对应的账面资产价值<br><span class="mhint">和股价对比看PB</span>' },
      { term: '经营现金流<br><small>Operating CF</small>', def: '经营活动产生的现金流入 − 流出<br>公司真正从业务中收到的现金<br><span class="mhint">应长期大于净利润，否则利润质量差</span>' },
    ]
  },
  高级: {
    desc: '进阶拆解指标',
    pairs: [
      { term: '权益乘数<br><small>Equity Multiplier</small>', def: '总资产 ÷ 净资产<br>衡量公司用了多少财务杠杆<br><span class="mhint">= 1 ÷ (1 − 资产负债率)</span>' },
      { term: '自由现金流<br><small>FCF</small>', def: '经营现金流 − 资本支出<br>巴菲特最看重的指标——公司真正可自由支配的钱<br><span class="mhint">有利润没现金=假繁荣</span>' },
      { term: 'EPS<br><small>每股收益</small>', def: '净利润 ÷ 总股本<br>每一股能分到多少利润<br><span class="mhint">持续增长是好信号，警惕稀释</span>' },
      { term: '杜邦分析<br><small>DuPont Analysis</small>', def: 'ROE = 净利率 × 资产周转率 × 权益乘数<br>拆解ROE的三大驱动因素<br><span class="mhint">帮你看清高ROE的来源是否健康</span>' },
      { term: '股东盈余<br><small>Owner Earnings</small>', def: '净利润 + 折旧摊销 − 维持性资本支出<br>巴菲特的"真实利润"概念<br><span class="mhint">比会计利润更接近经济现实</span>' },
      { term: '经济商誉<br><small>Economic Goodwill</small>', def: '市值 − 净资产<br>超过账面价值的市场认可——品牌、客户忠诚度<br><span class="mhint">巴菲特：最好的企业有巨大的经济商誉</span>' },
      { term: '利息保障倍数<br><small>Interest Coverage</small>', def: '息税前利润(EBIT) ÷ 利息费用<br>衡量公司赚的钱够付几次利息<br><span class="mhint">>5倍安全，<2倍危险</span>' },
      { term: '资本回报率<br><small>ROIC</small>', def: '税后营业利润 ÷ (净资产 + 有息负债)<br>衡量公司投入资本的真实回报率<br><span class="mhint">>15%说明有护城河</span>' },
      { term: '每股经营现金流<br><small>CFPS</small>', def: '经营现金流 ÷ 总股本<br>每一股对应的真实现金收入<br><span class="mhint">应长期高于EPS，否则利润质量存疑</span>' },
      { term: '扣非净利润<br><small>Recurring Profit</small>', def: '净利润 − 非经常性损益<br>排除卖资产、补贴等一次性收入后的真实利润<br><span class="mhint">看公司主业赚没赚钱，这个指标最准</span>' },
      { term: '毛利率趋势', def: '连续3年毛利率是否稳定或提升<br>评估公司竞争力的动态视角<br><span class="mhint">毛利率持续下降=护城河在变窄</span>' },
      { term: '自由现金流收益率<br><small>FCF Yield</small>', def: '自由现金流 ÷ 市值<br>类似PE，但用真实现金而非会计利润<br><span class="mhint">>5%不错，>10%很好</span>' },
    ]
  }
}
