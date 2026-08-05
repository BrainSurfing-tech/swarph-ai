"""
adaptive_copywriting.py — Dynamic Copywriting, Mesh Grounding & Allowlist Extraction Protocol

Integrates:
1. swarph brain-ask (vector memory substrate) & swarph codegraph (AST code index).
2. Elastic length allocation: ~2,500 chars baseline, expanding to 8,000–18,000+ chars for technical depth.
3. Allowlist Extraction Security Model: ONLY explicitly permitted public interface contracts,
   abstract architecture diagrams, and sanitized public signatures are extracted for whitepapers.
   All implementation bodies, multi-line docstring design logs, credentials, and internal state are ABSENT BY DEFAULT.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import re
import subprocess

class PrivacyLevel(Enum):
    PUBLIC = "PUBLIC"                         # Unrestricted public publishing
    ALLOWLIST_EXTRACTED = "ALLOWLIST_EXTRACTED" # Extracted public interface contracts only (absent by default)
    CONFIDENTIAL = "CONFIDENTIAL"             # Internal only (never publish)

@dataclass
class AdaptiveLengthPolicy:
    mode: str = "adaptive"
    baseline_chars: int = 2500
    min_chars: int = 1500
    allow_expansion: bool = True
    privacy_level: PrivacyLevel = PrivacyLevel.ALLOWLIST_EXTRACTED
    density_score: float = 0.0
    recommended_target_chars: int = 2500

def extract_allowlist_public_contract(code_snippet: str) -> str:
    """
    Allowlist Extraction Model:
    Extracts ONLY public class/def signatures, public type annotations, and the FIRST SUMMARY LINE
    of docstrings (API contract summary). All multi-line docstring design records, incident logs,
    implementation bodies, private credentials, and internal IPs are ABSENT BY DEFAULT.
    """
    lines = code_snippet.splitlines()
    extracted_lines = []
    
    in_docstring = False
    docstring_first_line_captured = False

    for line in lines:
        stripped = line.strip()
        # Allow public class & function signatures
        if stripped.startswith(("class ", "def ", "async def ", "export ", "interface ", "type ")) and not stripped.startswith("def _"):
            extracted_lines.append(line)
            in_docstring = False
            docstring_first_line_captured = False
        # Allow FIRST LINE of docstring (API summary line), drop multi-line docstring bodies
        elif '"""' in stripped or "'''" in stripped:
            if not in_docstring:
                in_docstring = True
                # Extract first line summary only
                cleaned = re.sub(r'["\']{3}', '', stripped).strip()
                if cleaned:
                    extracted_lines.append(f'    """ {cleaned} """')
                docstring_first_line_captured = True
            else:
                in_docstring = False
                docstring_first_line_captured = False
        elif in_docstring:
            # Drop multi-line docstring body (design/incident log safeguard)
            continue
        elif stripped in ("pass", "...", "return") or stripped.startswith("# Public API"):
            extracted_lines.append(line)

    if not extracted_lines:
        return "# [ALLOWLIST EXTRACTION]: Only public interface contracts are exposed."

    return "\n".join(extracted_lines)

def gather_mesh_context(query: str, repo: str = "swarph-ai") -> Dict[str, str]:
    """
    Pulls grounded semantic context from swarph brain-ask and swarph codegraph.
    Respects peer capability boundaries and allowlist extraction rules.
    """
    context_data = {"brain_context": "", "codegraph_context": ""}

    # 1. Gather memory context via brain-ask
    try:
        brain_out = subprocess.check_output(
            ["swarph", "brain-ask", query],
            stderr=subprocess.DEVNULL, timeout=8
        ).decode("utf-8")
        context_data["brain_context"] = brain_out.strip()
    except Exception:
        context_data["brain_context"] = "brain-ask unavailable or un-credentialed"

    # 2. Gather AST & code context via codegraph (repo-scoped by peer token)
    try:
        cg_out = subprocess.check_output(
            ["python3", "-m", "codegraph_index.query_cli", "--repo", repo, "--query", query],
            stderr=subprocess.DEVNULL, timeout=8
        ).decode("utf-8")
        context_data["codegraph_context"] = extract_allowlist_public_contract(cg_out.strip())
    except Exception:
        context_data["codegraph_context"] = f"codegraph query for repo '{repo}' requires peer capability grant"

    return context_data

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

def build_adaptive_system_prompt(title: str, context: str, policy: Optional[AdaptiveLengthPolicy] = None) -> str:
    """
    Constructs an LLM generation prompt with elastic length & allowlist extraction directives.
    """
    if policy is None:
        policy = AdaptiveLengthPolicy()

    analysis = assess_content_density(context)
    policy.density_score = analysis["density_score"]
    policy.recommended_target_chars = analysis["recommended_target_chars"]

    prompt = f"""
You are an expert technical author, security auditor, and SEO strategist.

TASK: Write an authoritative article titled: "{title}".

SECURITY & EXTRACTION LEVEL: {policy.privacy_level.value}
- ALLOWLIST EXTRACTION MODEL: Expose ONLY public interface contracts, sanitized class/def signatures, docstring 1-line summaries, and abstract architectural models.
- Multi-line docstring bodies (design logs/incident records), implementation logic, private credentials, internal IPs, and secret tokens are ABSENT BY DEFAULT.
- Retain high-level spatial topology models and mathematical formulations.

SOURCE MATERIAL & CONTEXT:
---
{context}
---

LENGTH & DENSITY GUIDELINES:
- Content Format Tier: {analysis['recommended_format']}
- Baseline Character Target: ~{policy.recommended_target_chars} characters (elastic).
- Minimum Character Floor: {policy.min_chars} characters.
- Elasticity: ALLOW EXPANSION. Do NOT artificially compress rich technical details, mathematical formulas, or code blocks.
- For concise source material, deliver a punchy, high-impact ~2,500 character article.
- For high-density technical material, expand naturally to cover all concepts thoroughly.

SEO & QUALITY REQUIREMENTS:
1. Use semantic H1, H2, H3 heading hierarchy.
2. Include an executive summary / key takeaways section.
3. Include an explicit disclaimer if discussing third-party technologies or vendor benchmarks.
4. Provide production-ready, sanitized code examples where applicable.
"""
    return prompt.strip()

if __name__ == "__main__":
    test_context = """
    class PublicInferenceEngine:
        \"\"\"
        Public inference engine contract summary line.

        DESIGN RECORD / INCIDENT LOG:
        Runs on lab-OVH only. DB path: ~/research/claude_mesh.db.
        Commander decision 2026-08-01: SO_PEERCRED bearer token bypass.
        \"\"\"
        def run_inference(self, vector: list) -> list:
            secret_key = "12345_secret"
            internal_ip = "10.0.0.1"
            return [1, 2, 3]
    """
    print("--- ALLOWLIST EXTRACTION TEST (DOCSTRING 1-LINE SUMMARY) ---")
    print(extract_allowlist_public_contract(test_context))
