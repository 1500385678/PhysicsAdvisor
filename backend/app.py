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


@app.get("/experiments")
def experiments():
    """经典实验清单(从 md 解析 H2 章节 + ### 实验名)"""
    out = []
    for fp in sorted(EXP_DIR.glob("*.md")):
        text = fp.read_text(encoding="utf-8")
        # 解析 ## <分支>(N 条) 块
        for m in re.finditer(r"^## (.+?)\((\d+) 条\)$", text, re.MULTILINE):
            out.append({"branch": m.group(1).strip(), "count": int(m.group(2)),
                        "source_file": fp.name})
    return {"count": len(out), "branches": out}
