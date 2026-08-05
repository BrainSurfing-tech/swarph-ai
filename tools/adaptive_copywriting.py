"""
adaptive_copywriting.py — Dynamic Copywriting, Mesh Grounding & Privacy Protocol

Integrates:
1. swarph brain-ask (vector memory substrate) & swarph codegraph (AST code index).
2. Elastic length allocation: ~2,500 chars baseline, expanding to 8,000–18,000+ chars for technical depth.
3. Privacy & Sensitivity Redaction Filter: sanitizes private credentials, internal IPs, and confidential keys before public release.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import re
import subprocess

class PrivacyLevel(Enum):
    PUBLIC = "PUBLIC"                     # Unrestricted public publishing
    INTERNAL_SANITIZED = "INTERNAL_SANITIZED" # Sanitized for public whitepapers (keys/IPs redacted)
    CONFIDENTIAL = "CONFIDENTIAL"         # Internal only (never publish)

@dataclass
class AdaptiveLengthPolicy:
    mode: str = "adaptive"
    baseline_chars: int = 2500
    min_chars: int = 1500
    allow_expansion: bool = True
    privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL_SANITIZED
    density_score: float = 0.0
    recommended_target_chars: int = 2500

def sanitize_public_copy(copy_text: str) -> str:
    """
    Sanitizes generated copy to ensure private credentials, tokens, internal IPs,
    and sensitive configuration strings are redacted before public publication.
    """
    sanitized = copy_text

    # Redact potential API keys & secret tokens
    sanitized = re.sub(r'(?i)(api[_-]?key|secret|bearer[_-]?token|pat)\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}["\']?', r'\1: "[REDACTED_KEY]"', sanitized)
    
    # Redact internal IPv4 addresses (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
    sanitized = re.sub(r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b', '[INTERNAL_IP]', sanitized)
    
    # Redact GitHub PAT tokens (ghp_..., gho_...)
    sanitized = re.sub(r'\b(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}\b', '[REDACTED_PAT]', sanitized)

    return sanitized

def gather_mesh_context(query: str, repo: str = "swarph-ai") -> Dict[str, str]:
    """
    Pulls grounded semantic context from swarph brain-ask and swarph codegraph.
    Respects current peer token capability boundaries.
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
        context_data["codegraph_context"] = cg_out.strip()
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
    Constructs an LLM generation prompt with elastic length & privacy directives.
    """
    if policy is None:
        policy = AdaptiveLengthPolicy()

    analysis = assess_content_density(context)
    policy.density_score = analysis["density_score"]
    policy.recommended_target_chars = analysis["recommended_target_chars"]

    prompt = f"""
You are an expert technical author, security auditor, and SEO strategist.

TASK: Write an authoritative article titled: "{title}".

PRIVACY & SENSITIVITY LEVEL: {policy.privacy_level.value}
- Strip or generalize any internal IP addresses, secret tokens, private API keys, or infrastructure credentials.
- Retain high-level architecture topologies, algorithms, and mathematical models while respecting privacy boundaries.

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
    We propose a zero-knowledge edge inference protocol using zk-SNARKs verified via \\pi = \\text{ProofGenerator}(x, w).
    Internal Gateway IP: 10.100.1.42 with bearer_token: "secret_tok_9941a".
    ```python
    def verify(x, pi): return True
    ```
    | Matrix | Latency |
    | Cloud | 380ms |
    | Edge | 12ms |
    """
    print("--- SANITIZATION TEST ---")
    print(sanitize_public_copy(test_context))
    print("\n--- SYSTEM PROMPT ---")
    print(build_adaptive_system_prompt("Frontier Edge Inference", test_context))
