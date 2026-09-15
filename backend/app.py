"""
PhysicsAdvisor · Phase 1 最小骨架 (2026-09-08 破冰版)
═══════════════════════════════════════════════════════
5 路由,启动:`uvicorn app:app --reload --port 8000`
数据源:`../data/knowledge.json` + `../data/experiments/*.md`
"""
import json
import re
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
KNOWLEDGE = json.loads((DATA_DIR / "knowledge.json").read_text(encoding="utf-8"))
EXP_DIR = DATA_DIR / "experiments"

app = FastAPI(title="PhysicsAdvisor API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    m = KNOWLEDGE["meta"]
    return {"ok": True, "schema": m["schema"], "concepts": m["total_concepts"],
            "formulas": m["total_formulas"], "cases": m["total_cases"],
            "experiments_files": len(list(EXP_DIR.glob("*.md")))}


@app.get("/graph")
def graph(limit: int = Query(50, ge=1, le=500)):
    """知识图谱:返回前 N 概念 + 它们的父子关系边"""
    concepts = KNOWLEDGE["concepts"][:limit]
    ids = {c["id"] for c in concepts}
    edges = [r for r in KNOWLEDGE["relations"]
             if r.get("type") == "parent_child"
             and r.get("source") in ids and r.get("target") in ids]
    return {"nodes": concepts, "edges": edges}


@app.get("/formulas")
def formulas(branch: Optional[str] = None):
    """公式列表,支持 ?branch=力学 过滤"""
    items = KNOWLEDGE["formulas"]
    if branch:
        items = [f for f in items if f.get("branch") == branch]
    return {"count": len(items), "items": items}


@app.get("/formulas/search")
def formulas_search(q: str = Query("", description="关键词:匹配公式名 / 变量符号 / 变量名"),
                    branch: Optional[str] = Query(None, description="分支过滤,如 力学")):
    """公式全文检索(2026-09-12 公式速查页配套)
    命中规则(任一满足):
      - 公式名(name) 包含 q(不区分大小写)
      - 变量符号(symbol) 包含 q(不区分大小写)
      - 变量名(name) 包含 q(不区分大小写)
    """
    items = KNOWLEDGE["formulas"]
    if branch:
        items = [f for f in items if f.get("branch") == branch]
    q_lower = q.strip().lower()
    if not q_lower:
        return {"q": q, "branch": branch, "count": len(items), "items": items}
    hits = []
    for f in items:
        if q_lower in f.get("name", "").lower():
            hits.append(f); continue
        for v in f.get("variables", []):
            if q_lower in v.get("symbol", "").lower() or q_lower in v.get("name", "").lower():
                hits.append(f); break
    return {"q": q, "branch": branch, "count": len(hits), "items": hits}


@app.get("/cases")
def cases(category: Optional[str] = None):
    """应用案例,支持 ?category=故事 / 应用 过滤"""
    items = KNOWLEDGE["cases"]
    if category:
        items = [c for c in items if c.get("category") == category]
    return {"count": len(items), "items": items}


# === 实验条目元数据字段(2026-09-16 实验页扩展) ===
_EXP_FIELDS = ["年代", "人物", "核心发现", "物理意义", "关键数据"]


def _parse_experiments_md(text: str, source_file: str, branch_hint: str = ""):
    """解析实验 md:
    - 01 经典实验.md 用 `### N. 实验名` 顶层标题 + `## <branch>(N 条)` 区块
    - 02-04 补充文件用 `#### N. 实验名` 子标题(在 ### 子分类下)+ `## <branch>(N 条)` 区块
    每条实验返回 {source_file, branch, id, name, era, people, discovery, significance, key_data}
    """
    items = []
    current_branch = branch_hint
    # 先扫描 ## <branch>(N 条) 段,记录每个分支
    branch_ranges = []  # [(branch, start_line, end_line)]
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        m = re.match(r"^## (.+?)\((\d+) 条\)$", ln.strip())
        if m:
            branch_ranges.append((m.group(1).strip(), i))
    # 边界:每个分支结束于下一个 ## 标题
    for idx, (b, start) in enumerate(branch_ranges):
        end = branch_ranges[idx + 1][1] if idx + 1 < len(branch_ranges) else len(lines)
        current_branch = b
        # 在 [start, end) 范围内找 ### N. 实验名 或 #### N. 实验名
        for j in range(start, end):
            line = lines[j].strip()
            # 标题格式:### <num>. <name> 或 #### <num>. <name>
            m2 = re.match(r"^#{3,4}\s+(\d+)\.\s+(.+)$", line)
            if not m2:
                continue
            num, name = int(m2.group(1)), m2.group(2).strip()
            # 抓后续 5 个元数据字段
            entry = {
                "source_file": source_file, "branch": current_branch,
                "id": f"EXP-{num:03d}", "name": name,
                "era": "", "people": "", "discovery": "",
                "significance": "", "key_data": ""
            }
            for k in range(j + 1, min(j + 30, end)):
                ln2 = lines[k].strip()
                # 遇到下一个标题(### 或 #### 或更高级)则中止
                if re.match(r"^#{2,}\s", ln2):
                    break
                for fld in _EXP_FIELDS:
                    pm = re.match(r"^- \*\*" + re.escape(fld) + r"\*\*\s*[:：]\s*(.+)$", ln2)
                    if pm:
                        entry[fld_to_key(fld)] = pm.group(1).strip()
                        break
            items.append(entry)
    return items


def fld_to_key(fld):
    return {"年代": "era", "人物": "people", "核心发现": "discovery",
            "物理意义": "significance", "关键数据": "key_data"}[fld]


@app.get("/experiments")
def experiments():
    """经典实验清单(2026-09-16 扩展):
    - 返回每个实验的完整元数据:id / name / branch / era / people / discovery / significance / key_data
    - 兼容 01(### N. 实验名)+ 02-04(#### N. 实验名) 两种标题格式
    """
    out = []
    for fp in sorted(EXP_DIR.glob("*.md")):
        text = fp.read_text(encoding="utf-8")
        out.extend(_parse_experiments_md(text, source_file=fp.name))
    return {"count": len(out), "items": out}


@app.get("/experiments/summary")
def experiments_summary():
    """经典实验分支汇总(保留旧端点:返回按分支的实验计数)"""
    out = []
    for fp in sorted(EXP_DIR.glob("*.md")):
        text = fp.read_text(encoding="utf-8")
        for m in re.finditer(r"^## (.+?)\((\d+) 条\)$", text, re.MULTILINE):
            out.append({"branch": m.group(1).strip(), "count": int(m.group(2)),
                        "source_file": fp.name})
    return {"count": len(out), "branches": out}
