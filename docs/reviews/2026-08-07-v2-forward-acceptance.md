# V2 前向验收报告（2026-08-07）

> **隐私与真实性声明：** 本报告中的人物、偏好、日期、候选地、行程、订单状态和事件均为虚构模拟数据，不对应任何真实个人或真实订单。本次未读取任何私人数据源。天气、余票、价格、酒店库存、景点开放/预约和现场人流等无法查询的动态事实全部按 `unknown` / `login_required` 处理；没有用测试夹具冒充实时事实。

## 1. 结论

**有条件通过。** 8 个前向场景的流程契约全部通过，8 份虚构 rank-1 日程全部通过确定性行程校验。无 Key、拒绝安装、伪 Key 失败、证据过期重验、长期潜力与本次适配分离、混合粒度归一化均符合 V2 规格。发现的脚本 UX、输入健壮性、评分语义、网络边界和发布安全问题均已修复并加入回归测试。

动态来源相关检查受工具与凭据限制：没有可用 web-search/interactive-browser，也没有用户授权的有效 AMap Key，因此实时天气、交通库存、酒店、景点与成功 AMap live smoke 为 `untestable`。伪 Key 通过真实 AMap 请求得到了可重复的 `invalid_key` 失败证据。

### 场景矩阵

| # | 场景 | 结果 | 关键证据 |
|---:|---|---|---|
| 1 | 三个虚构夏季候选，天气/人流风险不同 | PASS（动态子项 untestable） | 只用虚构季节风险夹具做条件排序；实时值全部 unknown/login_required；完整/备选/延期/pending 均出现 |
| 2 | 超过三个候选快速淘汰 | PASS | 5 个候选先筛到 3 个，没有为全部候选生成详细路线；未把缺证据解释为 fail |
| 3 | 出发超过 14 天 | PASS | 没有精确天气、温度或降雨概率；只保留季节风险与临近复核门槛 |
| 4 | 无 Key 且用户拒绝安装 | PASS | capability=`installed_but_unconfigured`；提供 AMap 三选项原文；选择零配置后继续 |
| 5 | 同意安装但 Key 验证失败 | PASS | 真实请求：`failed_stage=geocode`、`code=invalid_key`、`completed_stages=[]`；没有回显 Key |
| 6 | 72 小时内 rank-1 失效切到 rank-2 | PASS（事件为虚构注入） | rank-2 超过 24h 的交通/酒店/天气/关闭/预约证据全部重置待验，不直接执行旧备份 |
| 7 | 高长期潜力、低本次适配 | PASS | 虚构多区域长线保留高长期潜力；4 天且拒绝裁剪触发 duration hard-gate fail，不进入评分 |
| 8 | 混合粒度 + 有限天数 | PASS | 原标签、规范化形态、`minimum_viable_days` 同时展示；实质裁剪需用户接受 |

自动契约检查结果：`scenario_contract_pass=8/8`；确定性行程检查结果：`itinerary_validation_pass=8/8`、每份 `issue_count=0`。临时输入与完整虚构响应保存在 `/tmp/adaptive-travel-planner-v2-acceptance/`，未进入仓库。

## 2. 全新用户安装走查

### 2.1 README 公开仓库路径

实际执行：

```text
$ git clone https://github.com/ryunana/adaptive-travel-planner-skill.git
$ cd adaptive-travel-planner-skill
$ cp templates/traveler-profile.template.md references/traveler-profile.md
$ git check-ignore references/traveler-profile.md
references/traveler-profile.md
$ npx -y skills@latest add ryunana/adaptive-travel-planner-skill -g -a codex -y
exit=0; installed=~/.agents/skills/adaptive-travel-planner; target=Codex
$ mkdir -p ~/.agents/skills
$ ln -s "$(pwd)" ~/.agents/skills/adaptive-travel-planner
$ readlink ~/.agents/skills/adaptive-travel-planner
/tmp/adaptive-travel-planner-v2-acceptance/adaptive-travel-planner-skill
$ test -r templates/portable-prompt.template.md
portable_prompt=readable
```

skills.sh 一行安装在隔离 HOME 中成功，基于当前公开 main；V2 合并发布后仍需重跑。当前本地 V2 树的官方 `.agents/skills` 手工链接也在全新隔离 HOME 中原样成功；画像路径被 Git 忽略，Skill 链接和便携提示词可读。README 同时链接 OpenAI 当前 Build Skills 文档并展示 skills.sh 徽章，没有改动用户配置。

**发布状态限制：** README 的公开 clone 当前只能得到尚未包含 V2 的 `main`，因此“公开新用户取得 V2”在发布前不可测试；发布后必须重跑。

### 2.2 本地 V2 树补充安装

从当前本地 V2 树克隆到 `/tmp` 后，重复画像复制、ignore 检查、Skill 链接、便携提示词与 capability 命令，全部成功：

```text
v2_resources=yes
capability.amap.state=installed_but_unconfigured
```

未发现失效 README 链接；`release_checks.py` 的资源与链接检查通过。

## 3. 前向场景证据

所有场景均使用明确标注的虚构用户、偏好、候选和事件。每个场景响应均包含一句话条件排序、动态字段状态、逐日 rank-1 行程、rank-2 简版路线与切换条件、延期理由、固定 `pending_gates` 和恰好一个聚焦问题。

实际检查命令：

```text
$ python3 /tmp/adaptive-travel-planner-v2-acceptance/check_scenarios.py
scenario_contract_pass=8/8
itinerary_validation_pass=8/8
```

场景 1 只把季节风险差异当作虚构夹具，精确天气、预警、余票、酒店、开放和人流均待查。场景 2 先按时长和虚构约束缩减候选，再仅对三个候选展开筛选。场景 3 不生成超出预报期的精确天气断言。

场景 4 的实际命令摘要：

```text
$ python3 scripts/check_capabilities.py --config /tmp/.../no-config.json
exit=0; amap.state=installed_but_unconfigured; configured=false; verified=false

$ python3 scripts/verify_amap.py --config /tmp/.../no-config.json
exit=2; failed_stage=configuration; error.code=missing_key
```

Skill 响应提供三个选项：安装并继续、零配置继续、继续且不再询问。虚构用户选择零配置继续后，没有持久化“不再询问”偏好。

场景 5 使用明确的非秘密伪 Key 向真实 AMap 端点发起验证：

```text
$ AMAP_API_KEY=<fake> python3 scripts/verify_amap.py --config /tmp/.../no-config.json --timeout 10
exit=1
state=failed
failed_stage=geocode
completed_stages=[]
error.code=invalid_key
error.infocode=10001
key_source=environment
```

输出没有 Key 内容；geocode 失败后没有继续 route/weather，增强模式没有被误报为 working。

场景 6 把 rank-1 失效明确标为虚构注入事件；切换后 rank-2 仅成为待重验首选，超过 24 小时的动态证据全部进入 pending。场景 7 将 `destination_potential` 与 `this_trip_suitability` 分开，时长失配且拒绝裁剪时输出 `decision_status=rejected`、`suitability_score=null`。场景 8 的通用混合粒度输出为：

```text
多区域长线 → 单城与近郊 5 日（minimum_viable_days=4，待用户接受）
单城候选 → 单城 4 日（minimum_viable_days=3）
```

缺少动态证据时，scorer 输出 `decision_status=insufficient_evidence`、`suitability_score=null` 并保留 `pending_gates`，没有为了填满排名而伪造动态维度分值。

## 4. 六脚本 UX 测试

覆盖 `check_capabilities.py`、`setup_amap.py`、`amap_cli.py`、`verify_amap.py`、`score_destinations.py` 和 `validate_itinerary.py`。

| 用例 | 最终结果 |
|---|---|
| 六个 `--help` | exit 0；都有 `usage:` 与人类可读说明 |
| 六个无参数 | 6/6 输出可解析 JSON；交互 setup 在无 stdin 时返回 `input_unavailable` |
| 六个非法参数 | 6/6 exit 2，JSON `error.code=invalid_arguments` |
| 缺配置文件 | 3/3 JSON；检测命令正常报告 unconfigured，网络命令精确报告 missing_key |
| 缺输入文件 | 2/2 JSON `invalid_input` |
| 非法 JSON | 2/2 JSON `invalid_input` |
| 合法 JSON、错误顶层/元素结构 | 4/4 非零退出且输出结构化 JSON，不再 traceback |
| 嵌套状态、证据、活动结构与非有限权重 | 6/6 非零退出；stdout 单一标准 JSON；stderr 无 traceback |
| 非正/非有限 timeout | 两个网络 CLI 共 10/10 exit 2 + JSON `invalid_arguments`；正有限 timeout 保持接受 |

`--help` 是成功输出而非错误，保留 argparse 的文本帮助；所有实际错误路径均为结构化 JSON。

## 5. Bug 清单

| ID | 严重级别 | 状态 | 问题 | 证据/处理 |
|---|---|---|---|---|
| B1 | Medium / UX | fixed | argparse 无参数/非法参数写 stderr 文本，setup 非交互 EOF traceback | 共享 JSON argument parser + setup EOF 错误；新增六脚本契约测试 |
| B2 | Medium / Reliability | fixed | 两个 JSON 输入脚本遇到错误顶层或数组元素结构时 traceback | 显式 schema-shape 检查 + 4 个回归用例 |
| B3 | Medium / Decision correctness | fixed | 相邻分数差比较会链式扩大平局组 | 改为与平局组最高分比较；回归 rank=`1,1,3` |
| B4 | Medium / Confidence semantics | fixed | 缺证据被 coverage 与 authority 重复惩罚 | authority 只对已有记录求平均；1/9 verified 回归 value=.111 |
| B5 | Medium / Reliability | fixed | geocode `location` 畸形时 traceback | 返回 `malformed_response` 且不继续 route/weather |
| B6 | High / Contract | fixed | scorer 对数组状态/证据、非有限或布尔权重与分数可能 traceback 或错误接受 | 完整候选 shape、枚举与有限数值验证；CLI 回归输出标准 JSON |
| B7 | High / Contract | fixed | itinerary 的非数组核心活动、数组证据状态与布尔活动上限可能 traceback 或错误接受 | 返回清晰 issue；动态来源/查询时间在提供时必须为非空字符串 |
| B8 | High / Reliability | fixed | 两个 AMap CLI 接受非正或非有限 timeout | 共享正有限数值解析器在任何网络请求前 exit 2 拒绝 |
| B9 | Medium / Reliability | fixed | HTTP 响应读取中断可能泄漏 traceback | `HTTPException` 映射为脱敏结构化 `network_error` |
| B10 | Medium / Installability | fixed | Codex 安装目录过时且父目录不存在；发现元数据为截断残句 | 使用当前 `.agents/skills`、skills.sh 安装与完整 64 字符描述；发布检查验证边界和基本一致性 |
| B11 | High / Supply chain | fixed | CI action 使用可变标签且 checkout 保留凭据 | 两个 job 均固定官方不可变版本并关闭凭据持久化；zizmor 无未抑制 finding |
| B12 | Critical / Decision correctness | fixed | hard gate 的 pass/fail 可与 unknown/login_required 证据矛盾 | 未知证据只允许 undecidable；pending gate 强制非空名称与精确处理动作 |
| B13 | High / Secret safety | fixed | 参数错误与非 TTY 隐藏输入可能回显 Key | 所有参数错误使用通用消息；GetPassWarning fail-closed 且不写配置 |
| B14 | High / JSON contract | fixed | 非标准常量、无限输入/响应及输出序列化可破坏严格 JSON | 全局严格解析/输出；本地输入 1 MiB、provider 响应 2 MiB 上限及边界回归 |
| B15 | High / Configuration safety | fixed | 损坏配置可被覆盖，任意已有父目录权限可被改变 | 损坏配置独立状态并逐字节保留；只保护默认或新建目录权限 |
| B16 | High / Provider validation | fixed | AMap 成功状态缺少端点结构、畸形本地参数仍可进入网络 | geocode/route/weather 分别验证容器与记录；地址、坐标、adcode 在网络前验证 |
| B17 | High / Release integrity | fixed | 非 UTF-8 文件 fail-open、非法 YAML 与 reference/fragment 链接漏检 | 混合编码 fail-closed；PyYAML safe_load；完整本地链接与 heading 检查 |
| I1 | Info / Release state | untestable | README 公网 clone 目前只能得到 main，不含 V2 | 发布后按同一走查重测 |

## 6. 已决策评分语义

平局采用 2.0 阈值与 competition ranking，每个候选与当前平局组最高分比较，不允许相邻差值链式扩张。三个虚构候选总分 90、88、86 时输出：

```text
A: rank=1, tied=true
B: rank=1, tied=true
C: rank=3, tied=false
```

置信度规则为：

```text
coverage = usable_records / possible_records
authority = average authority of usable records, or 0 with no usable records
value = coverage * authority
level = high when value >= 0.8, medium when value >= 0.5, otherwise low
```

`references/scoring-model.md` 已记录公式、权威权重与 level 阈值。1 个 verified / 9 个 possible 的回归结果为 coverage≈0.111、authority=1.0、value≈0.111。

## 7. 不可测试项

| 项目 | 原因 | 当前处理 |
|---|---|---|
| 实时天气、预警、景区微气候 | 无 web-search/browser | `unknown`，不生成精确天气 |
| 交通余票 | 无用户登录会话 | `login_required`，列入 pending gate |
| 酒店实时价格/库存 | 无浏览器/登录渠道 | `unknown` / `login_required` |
| 景点开放、预约、退改 | 无浏览器/官方账号渠道 | `unknown` / `login_required` |
| 实时人流 | 无可靠当前来源 | `unknown` |
| 有效 Key 的 AMap 成功 live smoke | 没有用户授权 Key | `untestable`；只验证伪 Key 失败路径 |
| 公网 clone 后的 V2 新用户体验 | V2 分支尚未推送 | 发布后重测 |

## 8. 最终验证

最终 V2 树包含结构化 CLI 错误、严格有界 JSON、候选/行程完整 shape 检查、hard-gate 证据一致性、AMap 端点与本地参数验证、损坏配置保护、真实 YAML/链接/隐私发布检查、模板和回归测试；本报告只记录可复现的最终行为，不依赖中间开发历史。

```text
$ python3 -m unittest discover -s tests
Ran 72 tests
OK

$ python3 scripts/release_checks.py
release checks passed: metadata, 17 resources, links, privacy

$ mypy scripts
Success: no issues found in 8 source files

$ python3 /tmp/adaptive-travel-planner-v2-acceptance/check_scenarios.py
scenario_contract_pass=8/8
itinerary_validation_pass=8/8

$ uvx zizmor .github/workflows/ci.yml
No findings to report
```

评分语义回归验证 rank=`1,1,3`、tied=`true,true,false`、1/9 verified confidence=`coverage .111 / authority 1.0 / value .111`、无已有记录时 authority=`0.0`。畸形候选/行程输入、矛盾 hard gate、布尔和非有限数值、timeout、输入/响应尺寸边界、AMap 中断与端点响应 shape、损坏配置、混合编码、非法 YAML、reference/fragment 链接均有回归；所有 CLI 错误保持单一严格 JSON、非零退出且 stderr 无 traceback/secret。AMap 畸形 location fixture 回归验证 geocode 阶段结构化 `malformed_response` 且不调用 route/weather。

仓库内容隐私扫描无命中；`git ls-remote --heads origin agent/china-destination-selection-v2` 无输出，确认未推送该分支。本次没有执行 push，也没有切换分支或改动 main。
