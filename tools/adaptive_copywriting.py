"""
adaptive_copywriting.py — Dynamic Copywriting & Whitepaper Generation Protocol

Provides elastic length allocation for AI article & whitepaper generation:
- Baseline target of ~2,500 characters for short-format / quick reads.
- Elastic upward expansion (8,000–15,000+ characters) for high-density technical topics
  containing code, benchmarks, or mathematical formulations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import re

@dataclass
class AdaptiveLengthPolicy:
    mode: str = "adaptive"
    baseline_chars: int = 2500
    min_chars: int = 1500
    allow_expansion: bool = True
    density_score: float = 0.0
    recommended_target_chars: int = 2500

def assess_content_density(context_text: str) -> Dict[str, Any]:
    """
    Evaluates information density of source material to determine optimal article length.
    """
    math_symbols = len(re.findall(r'(\$\$.*?\$\$|\\\[.*?\\\]|\$|\\[a-zA-Z]+)', context_text))
    code_blocks = len(re.findall(r'```[\s\S]*?```', context_text))
    tables = len(re.findall(r'\|.*?\|', context_text))
    word_count = len(context_text.split())

    # Density calculation score
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
    Constructs an LLM generation prompt with elastic length directives based on source density.
    """
    if policy is None:
        policy = AdaptiveLengthPolicy()

    analysis = assess_content_density(context)
    policy.density_score = analysis["density_score"]
    policy.recommended_target_chars = analysis["recommended_target_chars"]

    prompt = f"""
You are an expert technical author and SEO strategist.

TASK: Write an authoritative article titled: "{title}".

SOURCE MATERIAL & CONTEXT:
---
{context}
---

LENGTH & DENSITY GUIDELINES:
- Content Format Tier: {analysis['recommended_format']}
- Baseline Character Target: ~{policy.recommended_target_chars} characters (elastic).
- Minimum Character Floor: {policy.min_chars} characters (prevent thin content).
- Elasticity: ALLOW EXPANSION. Do NOT artificially compress rich technical details, mathematical formulas, or code blocks.
- If the source material is concise, deliver a punchy, high-impact ~2,500 character article.
- If technical data, code, or benchmark matrices are present, expand naturally to cover all concepts thoroughly.

SEO & QUALITY REQUIREMENTS:
1. Use semantic H1, H2, H3 heading hierarchy.
2. Include an executive summary / key takeaways section.
3. Include an explicit disclaimer if discussing third-party technologies or vendor benchmarks.
4. Provide production-ready, typed code examples where applicable.
"""
    return prompt.strip()

if __name__ == "__main__":
    test_context = """
    We propose a zero-knowledge edge inference protocol using zk-SNARKs verified via \\pi = \\text{ProofGenerator}(x, w).
    ```python
    def verify(x, pi): return True
    ```
    | Matrix | Latency |
    | Cloud | 380ms |
    | Edge | 12ms |
    """
    result = assess_content_density(test_context)
    print("Assessment Result:", result)
    print("\n--- System Prompt ---\n")
    print(build_adaptive_system_prompt("Frontier Edge Inference", test_context))
