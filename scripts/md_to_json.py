#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md_to_json.py — 物理知识资产解析器

扫描 _PhysicsLib/ 下所有主题 md 文件(01-10 各主题文件夹 + 物理公式/),
解析为结构化 JSON,输出到 data/knowledge.json。

Schema 0.3.0:
{
  "meta": {
    "schema": "0.3.0",
    "generated_at": "2026-08-26T...",
    "source_dir": "_PhysicsLib",
    "total_files": 10,
    "total_words": 29084,
    "total_concepts": 194,
    "total_relations": 416,
    "total_branches": 10
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
      "parent_id": null,              // H2 顶层概念,无父
      "child_count": 3,                // 直接子节点数(H3)
      "source_file": "..."
    }
  ],
  "relations": [
    {"source": "01", "target": "01-物理起源与演变", "type": "branch_topic"},
    {"source": "01-物理起源与演变", "target": "01-01-001", "type": "topic_concept"},
    {"source": "01-01-001", "target": "01-01-002", "type": "parent_child"},
    {"source": "01-物理起源与演变", "target": "02-01-005", "type": "cross_ref",
     "evidence": "牛顿"}
  ],
  "branches": [
    {"id": "01", "name": "物理起源与演变", "topic_count": 1, "concept_count": 18}
  ]
}

变更记录:
- 0.1.0 (2026-08-24): 扫描 _PhysicsLib/ 主题 md,输出 topics 数组(10 主题 / 29084 字)。
- 0.2.0 (2026-08-25): 新增 concepts 数组(从 10 主题 md 抽取 H2/H3 概念节点),
                    为 Phase 0 知识图谱奠基;meta 加 total_concepts。
- 0.3.0 (2026-08-26): 新增 relations 关系层 + branches 汇总:
                    - branch_topic   (分支 → 主题) N 条
                    - topic_concept  (主题 → 概念) N 条
                    - parent_child   (H2 概念 → H3 概念) N 条
                    - cross_ref      (主题 → 跨主题概念,基于名称共现) N 条
                    概念新增 parent_id / child_count;meta 加 total_relations / total_branches。
                    为 Phase 0 知识图谱可查询/可视化奠基。
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
      - parent_id:H3 指向同 topic 的上一个 H2;H2 为 null

    返回:概念节点列表,每项含 id / name / branch / branch_name /
                       topic_id / level / parent_id / child_count / source_file
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
        last_h2_id = None
        for h in topic.get("headings", []):
            if h["level"] not in (2, 3):
                continue
            seq += 1
            if h["level"] == 2:
                # H2 顶层:parent 为 None
                concepts.append({
                    "id": f"{branch}-{dir_seq}-{seq:03d}",
                    "name": h["text"],
                    "branch": branch,
                    "branch_name": branch_name,
                    "topic_id": topic_id,
                    "level": h["level"],
                    "parent_id": None,
                    "child_count": 0,  # 后处理
                    "source_file": source_file,
                })
                last_h2_id = concepts[-1]["id"]
            else:
                # H3 子节点:parent 是同 topic 的上一个 H2
                concepts.append({
                    "id": f"{branch}-{dir_seq}-{seq:03d}",
                    "name": h["text"],
                    "branch": branch,
                    "branch_name": branch_name,
                    "topic_id": topic_id,
                    "level": h["level"],
                    "parent_id": last_h2_id,
                    "child_count": 0,
                    "source_file": source_file,
                })
    return concepts


def annotate_child_counts(concepts: list) -> list:
    """为每个 H2 概念补 child_count(直接 H3 子节点数)。"""
    counts = {}
    for c in concepts:
        if c["level"] == 3 and c["parent_id"]:
            counts[c["parent_id"]] = counts.get(c["parent_id"], 0) + 1
    for c in concepts:
        if c["level"] == 2:
            c["child_count"] = counts.get(c["id"], 0)
    return concepts


def normalize_concept_name(name: str) -> str:
    """规范化概念名用于共现匹配:去尾部问号/句号/空白。"""
    return name.strip().rstrip("？?。.!！").strip()


def build_relations(topics: list, concepts: list) -> list:
    """构建四类关系边。

    1. branch_topic   (分支 → 主题)    N = sum(topic per branch)
    2. topic_concept  (主题 → 概念)    N = total_concepts
    3. parent_child   (H2 概念 → H3 概念)  N = H3 count
    4. cross_ref      (主题 → 跨主题概念,基于概念名共现) N = 去重后

    去重策略:cross_ref 同 (source_topic, target_concept) 只保留 1 条,
              evidence 记录触发匹配的概念名。
    """
    relations = []
    seen = set()  # 用于跨引用去重

    # 1. branch → topic
    for t in topics:
        relations.append({
            "source": t["branch"],
            "target": t["id"],
            "type": "branch_topic",
        })

    # 2. topic → concept
    for c in concepts:
        relations.append({
            "source": c["topic_id"],
            "target": c["id"],
            "type": "topic_concept",
        })

    # 3. H2 → H3 父子边
    for c in concepts:
        if c["level"] == 3 and c["parent_id"]:
            relations.append({
                "source": c["parent_id"],
                "target": c["id"],
                "type": "parent_child",
            })

    # 4. 跨主题引用 —— 主题 A 的正文里出现概念 B 的名字 → cross_ref(A, B)
    # 建索引:name_norm → [(concept_id, branch)]
    name_index: dict = {}
    for c in concepts:
        norm = normalize_concept_name(c["name"])
        # 过滤太短/太通用的名字,避免误匹配
        if 2 <= len(norm) <= 12:
            name_index.setdefault(norm, []).append(c["id"])

    # 主题 → 自身概念 id 集合(避免自指)
    topic_self_ids: dict = {}
    for t in topics:
        topic_self_ids[t["id"]] = {c["id"] for c in concepts if c["topic_id"] == t["id"]}

    # 主题 → 自身所有概念名规范化集合(避免同主题内互引)
    topic_self_names: dict = {}
    for t in topics:
        topic_self_names[t["id"]] = {
            normalize_concept_name(c["name"])
            for c in concepts
            if c["topic_id"] == t["id"]
        }

    for t in topics:
        content = t["content"]
        topic_id = t["id"]
        for norm_name, target_ids in name_index.items():
            if norm_name in topic_self_names.get(topic_id, set()):
                # 同主题内的名字不算跨主题引用(主题→概念已覆盖)
                continue
            if norm_name in content:
                for target_id in target_ids:
                    if target_id in topic_self_ids.get(topic_id, set()):
                        continue
                    key = (topic_id, target_id, "cross_ref")
                    if key in seen:
                        continue
                    seen.add(key)
                    relations.append({
                        "source": topic_id,
                        "target": target_id,
                        "type": "cross_ref",
                        "evidence": norm_name,
                    })

    return relations


def build_branches(topics: list, concepts: list) -> list:
    """汇总每个分支:topic 数 / 概念数 / 主题列表。"""
    from collections import Counter

    topic_per_branch: dict = {}
    for t in topics:
        topic_per_branch.setdefault(t["branch"], []).append(t["id"])

    concept_per_branch: dict = Counter(c["branch"] for c in concepts)

    # 标题映射:branch → branch_name(用第一个 topic 的 title)
    branch_name_map: dict = {}
    for t in topics:
        branch_name_map.setdefault(t["branch"], t["title"])

    branches = []
    for b in sorted(topic_per_branch.keys()):
        branches.append({
            "id": b,
            "name": branch_name_map.get(b, b),
            "topic_count": len(topic_per_branch[b]),
            "concept_count": concept_per_branch.get(b, 0),
            "topic_ids": topic_per_branch[b],
        })
    return branches


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
    concepts = annotate_child_counts(concepts)
    # 关系层抽取(分支/主题/概念/跨引用)
    relations = build_relations(topics, concepts)
    # 分支汇总
    branches = build_branches(topics, concepts)

    # 关系按类型统计
    from collections import Counter
    rel_type_counts = Counter(r["type"] for r in relations)

    payload = {
        "meta": {
            "schema": "0.3.0",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_dir": "_PhysicsLib",
            "total_files": len(topics),
            "total_words": total_words,
            "total_concepts": len(concepts),
            "total_relations": len(relations),
            "total_branches": len(branches),
            "relation_breakdown": dict(rel_type_counts),
        },
        "topics": topics,
        "concepts": concepts,
        "relations": relations,
        "branches": branches,
    }

    # 输出
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] 解析 {len(topics)} 个主题 md")
    print(f"     字数: {total_words}")
    print(f"     概念: {len(concepts)} (H2={sum(1 for c in concepts if c['level']==2)}, "
          f"H3={sum(1 for c in concepts if c['level']==3)})")
    print(f"     关系: {len(relations)} {dict(rel_type_counts)}")
    print(f"     分支: {len(branches)}")
    print(f"     输出: {OUTPUT_PATH.relative_to(WEB_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
