"""
adaptive_copywriting.py — Broad-Read Grounding & Provenance-Gated Copywriting Protocol

Commander Directive:
- READ: BROAD — Access all brain hemispheres & codebase files to ground whitepapers in truth.
- SHOW: GATED — Gated at the PUBLISH boundary via explicit source provenance tracking.

Architecture:
1. Broad-Read Context Gathering: Queries vector memory (brain-ask) and codegraph index across repos.
2. Provenance Tracking: Every extracted snippet carries explicit source tags ([PROVENANCE: repo/path#symbol]).
3. Synthesis Classification: AI-synthesized prose is tagged with [SYNTHESIS].
4. Publish-Gate Check: Reviewers evaluate source publishability directly from provenance tags.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import re
import subprocess

class ContentSourceType(Enum):
    CODEGRAPH = "CODEGRAPH"
    BRAIN_MEMORY = "BRAIN_MEMORY"
    SYNTHESIS = "SYNTHESIS"

@dataclass
class ProvenanceRecord:
    source_type: ContentSourceType
    repo: str
    file_path: str
    symbol_or_lines: str = ""
    snippet: str = ""
    is_confidential_source: bool = False

@dataclass
class AdaptiveLengthPolicy:
    mode: str = "adaptive"
    baseline_chars: int = 2500
    min_chars: int = 1500
    allow_expansion: bool = True
    density_score: float = 0.0
    recommended_target_chars: int = 2500

def gather_broad_mesh_context(query: str, repos: Optional[List[str]] = None) -> List[ProvenanceRecord]:
    """
    Broad-Read Gathering (Commander Directive):
    Reads across memory and codebase hemispheres to ground copy in truth.
    Attaches explicit ProvenanceRecords to every extracted snippet.
    """
    if repos is None:
        repos = ["swarph-ai", "brainsurfing.tech", "mesh-gateway"]

    provenance_list: List[ProvenanceRecord] = []

    # 1. Broad Read: Memory Hemisphere (brain-ask)
    try:
        brain_out = subprocess.check_output(
            ["swarph", "brain-ask", query],
            stderr=subprocess.DEVNULL, timeout=10
        ).decode("utf-8").strip()
        if brain_out:
            provenance_list.append(ProvenanceRecord(
                source_type=ContentSourceType.BRAIN_MEMORY,
                repo="brain_memory",
                file_path="gbrain/pglite",
                symbol_or_lines="vector_search",
                snippet=brain_out
            ))
    except Exception:
        pass

    # 2. Broad Read: Codebase Hemisphere (codegraph)
    for repo in repos:
        try:
            cg_out = subprocess.check_output(
                ["python3", "-m", "codegraph_index.query_cli", "--repo", repo, "--query", query],
                stderr=subprocess.DEVNULL, timeout=10
            ).decode("utf-8").strip()
            if cg_out:
                provenance_list.append(ProvenanceRecord(
                    source_type=ContentSourceType.CODEGRAPH,
                    repo=repo,
                    file_path=f"codegraph_index/{repo}",
                    symbol_or_lines="query_match",
                    snippet=cg_out
                ))
        except Exception:
            pass

    return provenance_list

def assess_content_density(context_text: str) -> Dict[str, Any]:
    """
    Evaluates information density of source material to determine optimal article length.
    """
    math_symbols = len(re.findall(r'(\$\$.*?\$\$|\\\[.*?\\\]|\$|\\[a-zA-Z]+)', context_text))
    code_blocks = len(re.findall(r'```[\s\S]*?```', context_text))
    tables = len(re.findall(r'\|.*?\|', context_text))
    word_count = len(context_text.split())

    density_score = (math_symbols * 2.5) + (code_blocks * 3.0) + (tables * 1.5) + (word_count / 200.0)

    if density_score >= 10.0:
        recommended_format = "EXHAUSTIVE_WHITEPAPER"
        recommended_chars = max(8000, min(18000, int(word_count * 5.5)))
    elif density_score >= 4.0:
        recommended_format = "DEEP_TECHNICAL_ARTICLE"
        recommended_chars = max(4500, min(8000, int(word_count * 4.5)))
    else:
        recommended_format = "COMPACT_QUICK_READ"
        recommended_chars = 2500

    return {
        "density_score": round(density_score, 2),
        "math_symbols_count": math_symbols,
        "code_blocks_count": code_blocks,
        "tables_count": tables,
        "raw_word_count": word_count,
        "recommended_format": recommended_format,
        "recommended_target_chars": recommended_chars,
    }

def build_provenance_system_prompt(title: str, records: List[ProvenanceRecord], policy: Optional[AdaptiveLengthPolicy] = None) -> str:
    """
    Builds LLM generation prompt enforcing Broad-Read Grounding & Provenance Attribution.
    """
    if policy is None:
        policy = AdaptiveLengthPolicy()

    context_str = ""
    for rec in records:
        context_str += f"\n[SOURCE PROVENANCE: {rec.repo} | {rec.file_path}#{rec.symbol_or_lines}]\n{rec.snippet}\n"

    analysis = assess_content_density(context_str)
    policy.density_score = analysis["density_score"]
    policy.recommended_target_chars = analysis["recommended_target_chars"]

    prompt = f"""
You are an expert technical author, security auditor, and SEO strategist.

COMMANDER DIRECTIVE — GROUNDED PROVENANCE & PUBLISH GATING:
- READ: BROAD — Use the provided codebase & brain memory context to ground every assertion in truth.
- SHOW: PROVENANCE-TAGGED — Attach [Source: repo/filepath] citations to every technical claim or code snippet.
- SYNTHESIS TAGGING: Tag any synthesized conceptual prose with [SYNTHESIS].

TASK: Write an authoritative technical whitepaper titled: "{title}".

SOURCE MATERIAL & GROUNDED CONTEXT:
---
{context_str}
---

LENGTH & DENSITY GUIDELINES:
- Content Format Tier: {analysis['recommended_format']}
- Baseline Character Target: ~{policy.recommended_target_chars} characters (elastic).
- Minimum Character Floor: {policy.min_chars} characters.
- Elasticity: ALLOW EXPANSION. Do NOT artificially compress rich technical details, mathematical formulas, or code blocks.

PUBLISH REVIEW REQUIREMENTS:
1. Maintain explicit [Source: ...] provenance tags so human reviewers can verify source publishability at the gate.
2. Flag all AI conceptual synthesis with [SYNTHESIS].
3. Provide production-ready, typed code examples with provenance tags.
"""
    return prompt.strip()

if __name__ == "__main__":
    test_records = [
        ProvenanceRecord(
            source_type=ContentSourceType.CODEGRAPH,
            repo="swarph-ai",
            file_path="tools/adaptive_copywriting.py",
            symbol_or_lines="assess_content_density",
            snippet="def assess_content_density(context_text: str) -> Dict[str, Any]: pass"
        ),
        ProvenanceRecord(
            source_type=ContentSourceType.BRAIN_MEMORY,
            repo="brain_memory",
            file_path="gbrain/pglite",
            symbol_or_lines="card_219_ruling",
            snippet="Commander directive: Broad read across hemispheres, gated at publish boundary."
        )
    ]
    print("--- PROVENANCE-GROUNDED SYSTEM PROMPT ---")
    print(build_provenance_system_prompt("Frontier Memory Protocol", test_records))
