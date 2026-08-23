#!/usr/bin/env python3
"""
md_to_json.py — 把 _PhysicsLib/ 下的主题 md 解析为结构化 JSON

输入:
  - _PhysicsLib/01_物理起源与演变/物理起源与演变.md
  - _PhysicsLib/02_物理分支与特点/物理分支与特点.md
  - ... (10 个主题文件夹,各 1 个 .md)
  - _PhysicsLib/物理公式/*.md (待 Phase 0 公式库补充,本脚本已支持)

输出:
  - data/knowledge.json — {
      "meta": {generated_at, total_files, total_words},
      "topics": [
        {
          "id": "01_物理起源与演变",
          "branch": "起源与演变",
          "title": "物理起源与演变",
          "file_path": "01_物理起源与演变/物理起源与演变.md",
          "content": "...全文...",
          "word_count": 1234,
          "headings": [{"level": 1, "text": "..."}],
          "first_heading": "...",
          "tags": ["01_物理起源与演变", "branch:起源与演变"]
        }
      ]
    }

设计原则:
  - 通用扫描,不写死主题(后续 Phase 0 公式库补充时直接复用)
  - 一份 JSON 一份知识,Web 端 fetch 后按 branch / id 检索
  - 不解析 LaTeX(留给公式库 LaTeX 化阶段),只取 H1/H2/H3 标题

用法:
  python3 scripts/md_to_json.py [--lib-dir ../] [--out data/knowledge.json]
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# 匹配 Markdown 标题: # / ## / ###
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
# 匹配前 30 个非空白字符作为 title fallback
TITLE_FALLBACK_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def parse_md_file(md_path: Path, topic_id: str) -> dict:
    """解析单个 md 文件为结构化 dict"""
    text = md_path.read_text(encoding="utf-8")
    headings = []
    for m in HEADING_RE.finditer(text):
        headings.append({
            "level": len(m.group(1)),
            "text": m.group(2).strip(),
        })
    # 取第一个 H1 作为 title
    h1 = next((h for h in headings if h["level"] == 1), None)
    title = h1["text"] if h1 else md_path.stem
    # 简单字数统计(中英混合,只数非空白)
    word_count = len(re.sub(r"\s", "", text))
    # 从 topic_id 解析 branch(去掉前缀数字_)
    branch = re.sub(r"^\d+_", "", topic_id)

    return {
        "id": topic_id,
        "branch": branch,
        "title": title,
        "file_path": str(md_path),
        "content": text,
        "word_count": word_count,
        "headings": headings,
        "first_heading": title,
        "tags": [topic_id, f"branch:{branch}"],
    }


def scan_lib(lib_dir: Path) -> list[dict]:
    """扫描 _PhysicsLib/ 下所有主题 md(支持 01_xxx/*.md 与 物理公式/*.md)"""
    topics: list[dict] = []
    if not lib_dir.exists():
        print(f"[WARN] lib_dir 不存在: {lib_dir}", file=sys.stderr)
        return topics

    # 模式 A: 01_物理起源与演变/物理起源与演变.md (10 主题)
    for sub in sorted(lib_dir.iterdir()):
        if not sub.is_dir():
            continue
        # 跳过 PhysicsWeb 自己
        if sub.name == "PhysicsWeb":
            continue
        # 跳过隐藏目录
        if sub.name.startswith("."):
            continue
        # 取该目录下第一个 .md
        md_files = sorted(sub.glob("*.md"))
        if not md_files:
            continue
        # 优先取与目录同名的 md,否则取第一个
        target = next(
            (m for m in md_files if m.stem == sub.name), md_files[0]
        )
        topics.append(parse_md_file(target, sub.name))

    # 模式 B: 物理公式/*.md(待补,本脚本已支持)
    formula_dir = lib_dir / "物理公式"
    if formula_dir.exists():
        for md in sorted(formula_dir.glob("*.md")):
            # 公式文件以文件名作为 topic_id
            topics.append(parse_md_file(md, f"formula_{md.stem}"))

    return topics


def build_knowledge(topics: list[dict]) -> dict:
    return {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "total_files": len(topics),
            "total_words": sum(t["word_count"] for t in topics),
            "schema_version": "0.1.0",
        },
        "topics": topics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="物理 md 资产 → JSON")
    parser.add_argument(
        "--lib-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="_PhysicsLib 根目录(默认 ../)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "knowledge.json",
        help="输出 JSON 路径",
    )
    args = parser.parse_args()

    topics = scan_lib(args.lib_dir)
    knowledge = build_knowledge(topics)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(knowledge, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] 解析 {len(topics)} 个主题 md → {args.out}")
    print(f"     总字数: {knowledge['meta']['total_words']}")
    for t in topics:
        print(f"     - {t['id']:30s} | {t['word_count']:>5d} 字 | {t['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
