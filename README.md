# PhysicsAdvisor

> 15-物理-Physics 行业 Web 项目 · 内部代号 PhysicsAdvisor

## 项目说明
基于张勇的 36 行业架构,PhysicsAdvisor 是 物理-Physics 行业的 Web 端顾问产品。

## 同步
- GitHub: https://github.com/1500385678/PhysicsAdvisor
- Gitee: https://gitee.com/architectzy/PhysicsAdvisor

## 自动化
- T4 每日 02:00 检查项目并更新开发计划
- T5 每日 03:00 完成小步开发并 commit + push

## 数据资产

`_PhysicsLib/` 是张勇沉淀的物理知识原始 md(10 个主题 + 物理公式库),
通过 `scripts/md_to_json.py` 解析为 `data/knowledge.json`(结构化 JSON)。

### Schema 演进

| 版本 | 日期 | 关键变化 |
|------|------|----------|
| 0.1.0 | 2026-08-24 | topics 数组(10 主题 / 29084 字) |
| 0.2.0 | 2026-08-25 | + concepts 数组(194 节点,H2+H3 抽取) |
| 0.3.0 | 2026-08-26 | + relations 关系层(389 条 4 类边) + branches 汇总 |

### 当前结构(0.3.0)

```json
{
  "meta":   { schema, total_files, total_concepts, total_relations, relation_breakdown },
  "branches":   [ {id, name, topic_count, concept_count, topic_ids} ],
  "topics":     [ {id, branch, title, content, word_count, headings, tags} ],
  "concepts":   [ {id, name, branch, topic_id, level, parent_id, child_count} ],
  "relations":  [ {source, target, type, [evidence]} ]
}
```

### 关系类型

| type | 数量 | 含义 | 示例 |
|------|----:|------|------|
| `branch_topic`  | 10  | 分支 → 主题         | `01` → `01-01_物理起源与演变` |
| `topic_concept` | 194 | 主题 → 概念         | `01-01_...` → `01-01-001` |
| `parent_child`  | 123 | H2 概念 → H3 子概念  | `01-01-001` → `01-01-002` |
| `cross_ref`     |  62 | 主题 → 跨主题被引用概念 | `01-01_...` → `02-02-006` (evidence: "万有引力定律") |

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
"
```
