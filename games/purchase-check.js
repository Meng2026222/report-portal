// ===== 价值投资 · 单笔投资前置自检问卷 =====
// 20题 · 5大模块 · 是/否评分 · 4档把握度

// ===== 模块定义 =====
const PC_MODULES = [
  { id:0, name:'基础认知', icon:'🧭', color:'#4fc3f7' },
  { id:1, name:'企业护城河', icon:'🏰', color:'#f0c040' },
  { id:2, name:'财务健康度', icon:'📊', color:'#8bc34a' },
  { id:3, name:'管理层与治理', icon:'👥', color:'#9c27b0' },
  { id:4, name:'估值与安全边际', icon:'💰', color:'#ff9800' }
];

// ===== 题库（20题） =====
const PC_QUESTIONS = [
  // ── 一、基础认知 ──
  { id:1, m:0, q:'我清晰了解该企业核心主营业务、靠什么赚钱？',
    h:'不了解企业怎么赚钱=赌博。至少能说清楚产品/服务卖给谁、为什么有人买。' },
  { id:2, m:0, q:'我清楚该企业营收结构、各业务占比、主要收入来源？',
    h:'单一业务占比>80%需格外关注行业风险；多元化要确认各业务都盈利。' },
  { id:3, m:0, q:'该行业未来3–5年需求整体稳定或向上？',
    h:'需求下滑的行业里选股事倍功半。想一下：这个行业5年后还会存在吗？' },
  { id:4, m:0, q:'行业竞争格局清晰，头部企业壁垒稳固，不易陷入价格战？',
    h:'价格战是利润杀手。格局好的行业通常CR3>50%且份额持续集中。' },

  // ── 二、企业护城河 ──
  { id:5, m:1, q:'企业具备明确护城河：品牌/渠道/专利/规模/成本/网络效应至少一项？',
    h:'没有护城河的企业利润迟早被竞争侵蚀。至少要有1项难以复制的优势。' },
  { id:6, m:1, q:'近5年毛利率、净利率整体稳定或提升，无持续下滑？',
    h:'毛利率持续下滑=护城河在变窄。查看5年趋势而非只看1年。' },
  { id:7, m:1, q:'竞争对手很难在3年内复制其核心优势？',
    h:'如果对手用钱就能砸出来的优势，不是真护城河。' },
  { id:8, m:1, q:'企业议价能力强，对上下游话语权较高？',
    h:'议价能力=能涨价不被抵制、能压款不被断供。关注应收账款占比。' },

  // ── 三、财务健康度 ──
  { id:9, m:2, q:'近5年自由现金流持续为正，盈利真实可变现？',
    h:'利润不是现金。自由现金流持续为负的企业可能纸面富贵。' },
  { id:10, m:2, q:'资产负债率合理，无高负债、暴雷隐患？',
    h:'不同行业负债率差异大，重点关注有息负债率和短期偿债能力。' },
  { id:11, m:2, q:'营收、利润近5年无大幅剧烈波动，盈利可持续？',
    h:'大起大落要么是周期股（需判断周期位置），要么经营不稳。' },
  { id:12, m:2, q:'无大额商誉、质押、违规担保、财务造假嫌疑？',
    h:'商誉/净资产>30%是预警线。实控人高比例质押是重大危险信号。' },

  // ── 四、管理层与治理 ──
  { id:13, m:3, q:'管理层诚信务实，无频繁减持、掏空企业、负面丑闻？',
    h:'管理层人品比能力更重要。持续减持=他们自己都不看好。' },
  { id:14, m:3, q:'分红稳定、合理，重视股东回报？',
    h:'持续分红且分红率合理的公司造假动机更低，也更尊重小股东。' },
  { id:15, m:3, q:'企业不盲目多元化、不乱跨界，聚焦主业？',
    h:'跨界多元化失败率极高。好公司通常在自己擅长的领域深耕。' },
  { id:16, m:3, q:'管理层战略清晰，不激进冒进？',
    h:'看管理层过往言行是否一致。过于乐观的业绩指引常常是陷阱。' },

  // ── 五、估值与安全边际 ──
  { id:17, m:4, q:'当前估值处于自身历史低位区间，我判断处于低估？',
    h:'看PE/PB历史分位。处于历史30%分位以下才谈得上低估。' },
  { id:18, m:4, q:'相比同行，估值合理或偏低，无明显泡沫？',
    h:'一个行业里最贵的那个不一定最好。对比同行的PE、PB、PS。' },
  { id:19, m:4, q:'最坏情景下，下跌空间可控，有安全边际？',
    h:'问自己：如果跌30%我能毫不犹豫加仓吗？不能说明安全边际不足。' },
  { id:20, m:4, q:'买入逻辑清晰，不是炒热点、听消息、追题材？',
    h:'如果无法用三句话说清买入理由，说明你对它不够了解。' }
];

// ===== 把握度档位 =====
const PC_TIERS = [
  { min:16, max:20, label:'极高把握', action:'可重仓', icon:'✅', color:'#4caf50',
    desc:'各项指标扎实，符合价值投资核心要求。在保持跟踪的前提下可以放心配置。',
    full:'✅ 极高把握 · 可重仓\n所有维度检查通过，这笔投资逻辑清晰、基本面扎实。继续保持跟踪，关注季报是否验证你的判断。' },
  { min:12, max:15, label:'中等把握', action:'轻仓试错', icon:'🟡', color:'#f0c040',
    desc:'部分维度存在不确定性。建议先用计划的1/3仓位建仓，留足加仓空间。',
    full:'🟡 中等把握 · 轻仓试错\n有亮点也有疑虑。先建观察仓，等年报或关键催化剂出现后再决定是否加仓。重点关注失分项能否改善。' },
  { min:8, max:11, label:'低把握', action:'观望，不建仓', icon:'🟠', color:'#ff9800',
    desc:'多个关键维度不达标。当前不是好买点。建议继续研究，等年报或季报后再评估。',
    full:'🟠 低把握 · 观望不建仓\n多个核心维度亮红灯。好公司也要有好价格+好时机。建议列入自选继续跟踪，现在不是扣扳机的时候。' },
  { min:0, max:7, label:'无把握', action:'直接放弃', icon:'🔴', color:'#f44336',
    desc:'风险远大于机会。建议放弃这笔交易，把资金留给更有把握的机会。',
    full:'🔴 无把握 · 直接放弃\n风险远大于机会。A股4000多只股票，放弃一个不可惜。把子弹留给真正看得懂、算得清的机会。' }
];

var pcState = null;

// ===== 开始 =====
function startPC() {
  document.getElementById('pcIntro').style.display = 'none';
  document.getElementById('pcScreen').style.display = 'block';
  document.getElementById('pcResult').style.display = 'none';

  pcState = {
    idx: 0,
    answers: [],
    total: PC_QUESTIONS.length
  };

  document.getElementById('pcTotal').textContent = PC_QUESTIONS.length;
  document.getElementById('pcProgressBar').style.width = '0%';
  showPCQuestion(0);
}

// ===== 显示题目 =====
function showPCQuestion(idx) {
  var item = PC_QUESTIONS[idx];
  var mod = PC_MODULES[item.m];
  var total = pcState.total;

  // Module badge
  var modEl = document.getElementById('pcModuleBadge');
  modEl.innerHTML = '<span class="tg" style="background:'+mod.color+'20;color:'+mod.color+';border:1px solid '+mod.color+'40">'+mod.icon+' '+mod.name+'</span>';

  // Question number bar
  document.getElementById('pcNum').textContent = idx + 1;
  document.getElementById('pcProgressBar').style.width = ((idx / total) * 100) + '%';

  // Question text
  document.getElementById('pcQText').textContent = item.q;

  // Reset button state
  var prev = pcState.answers[idx];
  document.getElementById('pcYesBtn').className = 'pc-btn' + (prev && prev.score===1 ? ' selected-yes' : '');
  document.getElementById('pcYesBtn').textContent = '✅ 是';
  document.getElementById('pcYesBtn').disabled = false;
  document.getElementById('pcNoBtn').className = 'pc-btn' + (prev && prev.score===0 ? ' selected-no' : '');
  document.getElementById('pcNoBtn').textContent = '❌ 否';
  document.getElementById('pcNoBtn').disabled = false;

  document.getElementById('pcHint').style.display = 'none';
}

// ===== 选择答案 =====
function selectPC(score) {
  var idx = pcState.idx;
  if (pcState.answers[idx] !== undefined) return;

  pcState.answers[idx] = { qId: PC_QUESTIONS[idx].id, score: score };

  var yesBtn = document.getElementById('pcYesBtn');
  var noBtn = document.getElementById('pcNoBtn');
  yesBtn.className = 'pc-btn' + (score===1 ? ' selected-yes' : '');
  noBtn.className = 'pc-btn' + (score===0 ? ' selected-no' : '');
  yesBtn.disabled = true;
  noBtn.disabled = true;

  // Show hint briefly
  var item = PC_QUESTIONS[idx];
  var hintEl = document.getElementById('pcHint');
  if (score === 0) {
    hintEl.innerHTML = '💡 ' + item.h;
    hintEl.style.display = 'block';
  }

  setTimeout(function() {
    yesBtn.disabled = false;
    noBtn.disabled = false;
    nextPC();
  }, 400);
}

// ===== 下一题 / 结束 =====
function nextPC() {
  pcState.idx++;
  if (pcState.idx >= pcState.total) {
    showPCResult();
    return;
  }
  showPCQuestion(pcState.idx);
}

// ===== 显示结果 =====
function showPCResult() {
  document.getElementById('pcScreen').style.display = 'none';
  document.getElementById('pcResult').style.display = 'block';

  // Calculate score
  var score = 0;
  var missed = [];
  var moduleScores = [0,0,0,0,0];
  var moduleTotals = [4,4,4,4,4];

  for (var i = 0; i < pcState.answers.length; i++) {
    var ans = pcState.answers[i];
    var q = PC_QUESTIONS[i];
    if (ans.score === 1) {
      score++;
      moduleScores[q.m]++;
    } else {
      missed.push({q: q, mod: PC_MODULES[q.m]});
    }
  }

  // Determine tier
  var tier = PC_TIERS[3];
  for (var t = 0; t < PC_TIERS.length; t++) {
    if (score >= PC_TIERS[t].min) { tier = PC_TIERS[t]; break; }
  }

  // ── Score circle ──
  document.getElementById('pcScoreNum').textContent = score;
  document.getElementById('pcScoreMax').textContent = '/20';
  document.getElementById('pcScoreRing').style.background =
    'conic-gradient('+tier.color+' 0%, '+tier.color+' '+((score/20)*100)+'%, var(--b1) '+((score/20)*100)+'%, var(--b1) 100%)';

  // ── Tier ──
  document.getElementById('pcTierIcon').textContent = tier.icon;
  document.getElementById('pcTierLabel').textContent = tier.label;
  document.getElementById('pcTierLabel').style.color = tier.color;
  document.getElementById('pcActionBadge').textContent = tier.action;
  document.getElementById('pcActionBadge').style.background = tier.color+'20';
  document.getElementById('pcActionBadge').style.color = tier.color;
  document.getElementById('pcActionBadge').style.borderColor = tier.color+'40';
  document.getElementById('pcTierDesc').textContent = tier.desc;

  // ── Module bars ──
  var modHtml = '';
  for (var m = 0; m < 5; m++) {
    var mod = PC_MODULES[m];
    var ms = moduleScores[m];
    var mt = moduleTotals[m];
    var pct = Math.round((ms/mt)*100);
    var icon = ms === mt ? '✅' : ms >= mt/2 ? '⚠️' : '❌';
    var s = ms === mt ? '' : ' <span style="color:var(--m5);font-size:10px">（失'+ (mt-ms) +'题）</span>';
    modHtml += '<div class="pc-mod-row">';
    modHtml += '<div class="pc-mod-hdr"><span>'+mod.icon+' '+mod.name+'</span><span>'+icon+' '+ms+'/'+mt+s+'</span></div>';
    modHtml += '<div class="pc-mod-barw"><div class="pc-mod-bar" style="width:'+pct+'%;background:'+mod.color+'"></div></div>';
    modHtml += '</div>';
  }
  document.getElementById('pcModules').innerHTML = modHtml;

  // ── Missed items ──
  if (missed.length > 0) {
    var missHtml = '<div class="pc-miss-title">📋 失分项分析（'+missed.length+'题）</div>';
    for (var j = 0; j < missed.length; j++) {
      var mq = missed[j];
      missHtml += '<div class="pc-miss-item"><div class="pc-miss-mod-tag" style="background:'+mq.mod.color+'20;color:'+mq.mod.color+';border-color:'+mq.mod.color+'30">'+mq.mod.icon+' '+mq.mod.name+'</div>';
      missHtml += '<div class="pc-miss-q">❌ '+mq.q.q+'</div>';
      missHtml += '<div class="pc-miss-hint">💡 '+mq.q.h+'</div></div>';
    }
    document.getElementById('pcMissed').innerHTML = missHtml;
    document.getElementById('pcMissed').style.display = 'block';
  } else {
    document.getElementById('pcMissed').style.display = 'none';
  }

  document.getElementById('pcProgressBar').style.width = '100%';
}

// ===== 重置 =====
function resetPC() {
  document.getElementById('pcResult').style.display = 'none';
  document.getElementById('pcScreen').style.display = 'none';
  document.getElementById('pcIntro').style.display = 'block';
  document.getElementById('pcProgressBar').style.width = '0%';
}
