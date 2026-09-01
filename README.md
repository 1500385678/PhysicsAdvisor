# PhysicsAdvisor

> 15-物理-Physics 行业 Web 项目 · 内部代号 PhysicsAdvisor

## 项目说明
基于张勇的 36 行业架构,PhysicsAdvisor 是 物理-Physics 行业的 Web 端顾问产品。

## 同步
- GitHub: https://github.com/1500385678/PhysicsAdvisor
- Gitee: https://gitee.com/architectzy/PhysicsAdvisor

## 自动化
- T4 每日 02:20 巡检项目 + 更新开发计划
- T5 每日 03:20 完成小步开发并 commit + push

## 数据资产

`_PhysicsLib/` 是张勇沉淀的物理知识原始 md(10 个主题 + 物理公式库),
通过 `scripts/md_to_json.py` 解析为 `data/knowledge.json`(结构化 JSON)。

### Schema 演进

| 版本 | 日期 | 关键变化 |
|------|------|----------|
| 0.1.0 | 2026-08-24 | topics 数组(10 主题 / 29084 字) |
| 0.2.0 | 2026-08-25 | + concepts 数组(194 节点,H2+H3 抽取) |
| 0.3.0 | 2026-08-26 | + relations 关系层(389 条 4 类边) + branches 汇总 |
| 0.4.0 | 2026-08-27 | + cases 案例层(24 条 2 类:故事 9 + 应用 15) |
| 0.5.0 | 2026-08-28 | + formulas 公式层(14 条力学公式 from `_PhysicsLib/物理公式/`) |

### 当前结构(0.5.0)

```json
{
  "meta":   {
    "schema": "0.5.0",
    "total_files": 10,
    "total_concepts": 194,
    "total_relations": 389,
    "total_branches": 10,
    "total_cases": 24,
    "total_formulas": 67,
    "formula_branch_breakdown": {"力学": 14, "电磁学": 15, "热学": 18, "光学": 20},
    "case_category_breakdown": {"故事": 9, "应用": 15}
  },
  "branches":   [ {id, name, topic_count, concept_count, topic_ids} ],
  "topics":     [ {id, branch, title, content, word_count, headings, tags} ],
  "concepts":   [ {id, name, branch, topic_id, level, parent_id, child_count} ],
  "relations":  [ {source, target, type, [evidence]} ],
  "cases":      [ {id, name, category, branch, summary, word_count, heading_level, section} ],
  "formulas":   [ {id, name, branch, branch_short, expression, expression_extra, variables, conditions, source_file} ]
}
```

### 关系类型

| type | 数量 | 含义 | 示例 |
|------|----:|------|------|
| `branch_topic`  | 10  | 分支 → 主题         | `01` → `01-01_物理起源与演变` |
| `topic_concept` | 194 | 主题 → 概念         | `01-01_...` → `01-01-001` |
| `parent_child`  | 123 | H2 概念 → H3 子概念  | `01-01-001` → `01-01-002` |
| `cross_ref`     |  62 | 主题 → 跨主题被引用概念 | `01-01_...` → `02-02-006` (evidence: "万有引力定律") |

### 公式层结构(formulas)

每条公式:
- `id` (如 `F-01-01`)
- `name` (中文名,如 "牛顿第二定律")
- `branch` / `branch_short` (如 "力学" / "01")
- `expression` (主公式 LaTeX,取首个 `$$ ... $$` 块)
- `expression_extra` (同一公式的附加表达 / 联立 / 等价)
- `variables` ([{symbol, name, unit}])
- `conditions` (适用条件)
- `source_file` (来源 md)

当前覆盖:**67 条**(力学 14 + 电磁学 15 + 热学 18 + 光学 20,from `data/formulas/01_力学公式.md` + `02_电磁学公式.md` + `03_热学公式.md` + `04_光学公式.md`),后续补近代物理到 100+。

### 案例层结构(cases)

每条案例:
- `id` (如 `C-故事-01-01` / `C-应用-08-01`)
- `name` (案例名)
- `category` (`故事` from 04_物理故事与传说 / `应用` from 08_物理应用与建模)
- `branch` / `summary` / `word_count` / `heading_level` / `section` / `source_file`

当前覆盖:**24 条**(9 故事 + 15 应用)。

### 查询示例

```bash
# 重新生成
python3 scripts/md_to_json.py

# 概念 + 父节点 + 引用
python3 -c "
import json
d = json.load(open('data/knowledge.json'))
# 查某概念的父链
c = next(c for c in d['concepts'] if c['id']=='01-01-002')
print(c['parent_id'], '->', c['id'], c['name'])
# 查某主题引用的所有跨主题概念
refs = [r for r in d['relations'] if r['source']=='01-01_物理起源与演变' and r['type']=='cross_ref']
print(len(refs), 'cross_refs')
# 查某分支的公式
formulas = [f for f in d['formulas'] if f['branch_short']=='01']
print(len(formulas), 'mechanics formulas')
# 查某类别的案例
stories = [c for c in d['cases'] if c['category']=='故事']
print(len(stories), 'stories')
"

# 列出所有公式(快速浏览)
python3 -c "
import json
d = json.load(open('data/knowledge.json'))
for f in d['formulas']:
    print(f\"{f['id']:>8}  {f['branch_short']}  {f['name']:<12}  {f['expression']}\")
"
```

## 变更记录

- **0902**:公式层扩到 04 光学分支(`data/formulas/04_光学公式.md` 20 条,覆盖几何光学三大定律/斯涅尔/全反射临界角/费马原理/菲涅尔反射率/薄透镜成像/透镜制造者/显微镜分辨极限/单缝衍射/双缝干涉/光栅衍射/布拉格衍射/多普勒(光)/马吕斯/布儒斯特/双折射/普朗克黑体辐射/爱因斯坦光电效应/康普顿散射/相对论速度叠加),公式数 47 → 67,`formula_branch_breakdown` 从 `{"力学": 14, "电磁学": 15, "热学": 18}` → `{"力学": 14, "电磁学": 15, "热学": 18, "光学": 20}`;🟡 P1 推进 1 步(4/5 公式分支就位,距 100 差 33,0903 近代物理 1 分支 15-20 条即可达 82-87)。
- **0901**:公式层扩到 03 热学分支(`data/formulas/03_热学公式.md` 18 条,覆盖状态方程/压强微观/平均动能/麦克斯韦分布/平均自由程/热一律/四过程/比热容/熵增/卡诺/玻尔兹曼熵/傅里叶/牛顿冷却/斯特藩-玻尔兹曼/维恩位移/杨-拉普拉斯/焦耳/麦克斯韦关系),公式数 29 → 47,`formula_branch_breakdown` 从 `{"力学": 14, "电磁学": 15}` → `{"力学": 14, "电磁学": 15, "热学": 18}`;🟡 P1 推进 1 步(距 100 差 53,后续 0902 光学 / 0903 近代物理)。
- **0831**:公式层扩到 02 电磁学分支(`data/formulas/02_电磁学公式.md` 15 条,覆盖库仑/电场/高斯/电势/电容/欧姆/电阻/焦耳/KCL/KVL/安培力/洛伦兹力/法拉第/楞次),公式数 14 → 29,`formula_branch_breakdown` 从 `{"力学": 14}` → `{"力学": 14, "电磁学": 15}`;🟡 P1 推进 1 步。
- **0829**:README 同步 schema 0.5.0(补 0.4.0 cases + 0.5.0 formulas 章节);删除冗余 `物理顾问开发架构与计划.md`(70% 重复 `项目开发计划.md`,🔴 阻塞级挂账 4 天解套),其"三件套讲解 / 现象库"独有理念已并入 `项目开发计划.md` 决策记录。
- **0826**:`md_to_json.py` schema 0.2.0 → 0.3.0 关系层,README 同步。
- **0824**:`md_to_json.py` 立项,schema 0.1.0。
