#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md_to_json.py — 物理知识资产解析器

扫描 _PhysicsLib/ 下所有主题 md 文件(01-10 各主题文件夹 + 物理公式/),
解析为结构化 JSON,输出到 data/knowledge.json。

Schema 0.2.0:
{
  "meta": {
    "schema": "0.2.0",
    "generated_at": "2026-08-25T...",
    "source_dir": "_PhysicsLib",
    "total_files": 10,
    "total_words": 29084,
    "total_concepts": 194
  },
  "topics": [
    {
      "id": "01-物理起源与演变",
      "branch": "01",
      "title": "物理起源与演变",
      "file_path": "_PhysicsLib/01_物理起源与演变/物理起源与演变.md",
      "content": "...",
      "word_count": 3193,
      "headings": [{"level": 1, "text": "..."}],
      "first_heading": "...",
      "tags": ["物理起源", "演变"]
    }
  ],
  "concepts": [
    {
      "id": "01-01-001",
      "name": "物理是什么",
      "branch": "01",
      "branch_name": "物理起源与演变",
      "topic_id": "01-01_物理起源与演变",
      "level": 2,
      "source_file": "_PhysicsLib/01_物理起源与演变/物理起源与演变.md"
    }
  ]
}

变更记录:
- 0.2.0 (2026-08-25): 新增 concepts 数组(从 10 主题 md 抽取 H2/H3 概念节点),
                    为 Phase 0 知识图谱奠基;meta 加 total_concepts。
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 路径配置 —— 脚本在 PhysicsWeb/scripts/,工作目录是 PhysicsWeb/
SCRIPT_DIR = Path(__file__).resolve().parent
WEB_DIR = SCRIPT_DIR.parent  # PhysicsWeb/
# PhysicsWeb/ 已经在 _PhysicsLib/ 下一级,源目录是 _PhysicsLib 本身
SOURCE_DIR = WEB_DIR.parent  # _PhysicsLib/
# 根视角(_PhysicsLib/),用于生成 file_path
ROOT_DIR = WEB_DIR.parent
OUTPUT_PATH = WEB_DIR / "data" / "knowledge.json"

# 主题文件夹正则:01_xxx, 02_xxx, ..., 10_xxx(允许两位数)
TOPIC_DIR_RE = re.compile(r"^(\d{1,2})_(.+)$")
# 主题 md 文件名同目录名:01_xxx/01_xxx.md 或 01_xxx/中文.md
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
WHITESPACE_RE = re.compile(r"\s+")


def count_words(text: str) -> int:
    """中文字数:统计非空白字符数(兼容 ASCII 字母)。"""
    return len(WHITESPACE_RE.sub("", text))


def parse_headings(content: str) -> list:
    """提取所有 markdown 标题 (H1-H6)。"""
    headings = []
    for line in content.splitlines():
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if text:
                headings.append({"level": level, "text": text})
    return headings


def extract_tags(branch_name: str, title: str) -> list:
    """从主题名中提取 2-4 字标签。"""
    # 简单分词:主题名通常为 4-8 字中文短语,提取 2-3 个标签
    # 例:"物理起源与演变" → ["物理起源", "演变"]
    # 规则:含"与"则按"与"拆,否则按 4 字一块拆
    if "与" in title:
        parts = title.split("与", 1)
        tags = [part.strip() for part in parts if part.strip()]
    else:
        # 4 字一拆
        tags = [title[i : i + 4] for i in range(0, len(title), 4) if title[i : i + 4]]
    tags.append("物理")  # 全局标签
    return tags


def find_topic_files(source_dir: Path) -> list:
    """扫描 _PhysicsLib/ 下所有主题 md 文件。

    规则:
      1. 顶层目录以 N_xxx 开头(N=1-2 位数字)的视为主题目录
      2. 主题目录下的 *.md 全部纳入
      3. 顶层"物理公式"目录(或其他非数字开头但有 md 的)也纳入
    排除:
      - PhysicsWeb/、README.md、PhysicsLibControl.md、.plan/、.git/
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"找不到源目录: {source_dir}")

    files = []
    for entry in sorted(source_dir.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        # 排除隐藏目录和非主题目录
        if name.startswith("."):
            continue
        # 主题目录:N_xxx
        m = TOPIC_DIR_RE.match(name)
        is_topic = bool(m)
        # 物理公式/等扩展库:非数字开头但有 md 也纳入
        has_md = any(entry.glob("*.md"))

        if is_topic:
            branch = m.group(1).zfill(2)  # 1 → 01
            for md in sorted(entry.glob("*.md")):
                files.append((branch, name, md))
        elif has_md and not name.startswith("PhysicsWeb"):
            # 扩展库(如"物理公式"):用 99 前缀
            for md in sorted(entry.glob("*.md")):
                files.append(("99", name, md))

    return files


def build_topic(branch: str, dir_name: str, md_path: Path, source_root: Path) -> dict:
    """从单个 md 文件构建 topic 字典。"""
    rel_path = md_path.relative_to(source_root.parent)
    content = md_path.read_text(encoding="utf-8")
    word_count = count_words(content)
    headings = parse_headings(content)
    first_heading = headings[0]["text"] if headings else md_path.stem
    title = dir_name.split("_", 1)[1] if "_" in dir_name else dir_name
    topic_id = f"{branch}-{dir_name}"
    tags = extract_tags(branch, title)
    return {
        "id": topic_id,
        "branch": branch,
        "title": title,
        "file_path": str(rel_path),
        "content": content,
        "word_count": word_count,
        "headings": headings,
        "first_heading": first_heading,
        "tags": tags,
    }


def extract_concepts(topics: list) -> list:
    """从 topics 列表中抽取核心概念节点(基于 H2/H3 标题)。

    规则:
      - H1 视为文件主题(已在 topic.first_heading),不作为概念节点
      - H2/H3 视为核心概念,生成扁平列表
      - 同一 topic 内按出现顺序连续编号
      - id 格式: {branch}-{dir_seq}-{NNNN} (如 01-01-001)

    返回:概念节点列表,每项含 id / name / branch / branch_name / topic_id / level / source_file
    """
    concepts = []
    for topic in topics:
        topic_id = topic["id"]
        branch = topic["branch"]
        branch_name = topic["title"]
        source_file = topic["file_path"]
        # 从 topic_id 解析 dir_seq:形如 "01-01_物理起源与演变"
        dir_seq = topic_id.split("-", 1)[1].split("_", 1)[0] if "-" in topic_id else "00"
        seq = 0
        for h in topic.get("headings", []):
            if h["level"] not in (2, 3):
                continue
            seq += 1
            concepts.append({
                "id": f"{branch}-{dir_seq}-{seq:03d}",
                "name": h["text"],
                "branch": branch,
                "branch_name": branch_name,
                "topic_id": topic_id,
                "level": h["level"],
                "source_file": source_file,
            })
    return concepts


def main() -> int:
    try:
        files = find_topic_files(SOURCE_DIR)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    if not files:
        print(f"[ERROR] 在 {SOURCE_DIR} 下未找到任何主题 md", file=sys.stderr)
        return 1

    # 解析
    topics = [build_topic(b, d, p, ROOT_DIR) for b, d, p in files]
    total_words = sum(t["word_count"] for t in topics)
    # 概念层抽取(基于 H2/H3 标题)
    concepts = extract_concepts(topics)

    payload = {
        "meta": {
            "schema": "0.2.0",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_dir": "_PhysicsLib",
            "total_files": len(topics),
            "total_words": total_words,
            "total_concepts": len(concepts),
        },
        "topics": topics,
        "concepts": concepts,
    }

    # 输出
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] 解析 {len(topics)} 个主题 md")
    print(f"     字数: {total_words}")
    print(f"     概念: {len(concepts)} (H2+H3 标题)")
    print(f"     输出: {OUTPUT_PATH.relative_to(WEB_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
