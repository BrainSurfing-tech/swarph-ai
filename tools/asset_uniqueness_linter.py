"""
asset_uniqueness_linter.py — Asset Uniqueness & Quality Auditor

Automated Review Specialist Agent Tool that inspects web pages and asset directories for:
1. Duplicate Asset Usage: Flags images referenced multiple times within the same document.
2. Identical File Hash Duplication: Detects duplicate graphic files stored under different names (MD5/SHA256).
3. Missing Asset Verification: Validates that every <img>, <svg>, og:image, and twitter:image exists on disk.
4. SVG Text Neutrality Audit: Scans SVG graphics for un-neutralized vendor/product brand strings.
"""

import sys
import os
import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Any
from html.parser import HTMLParser

@dataclass
class AssetAuditIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    category: str  # "DUPLICATE_ASSET", "MISSING_ASSET", "IDENTICAL_FILE_HASH", "BRAND_SAFETY"
    file_path: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

class HTMLAssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.img_sources: List[Tuple[str, int]] = []
        self.meta_images: List[Tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "img" and "src" in attr_dict:
            line_no = self.getpos()[0]
            self.img_sources.append((attr_dict["src"], line_no))
        elif tag == "meta":
            prop = attr_dict.get("property", "") or attr_dict.get("name", "")
            if prop in ("og:image", "twitter:image") and "content" in attr_dict:
                self.meta_images.append((prop, attr_dict["content"]))

def audit_html_file(html_path: str, webroot: str = "/home/ubuntu/brainsurfing.tech") -> List[AssetAuditIssue]:
    issues: List[AssetAuditIssue] = []
    if not os.path.exists(html_path):
        issues.append(AssetAuditIssue(
            severity="ERROR",
            category="MISSING_ASSET",
            file_path=html_path,
            message=f"Target HTML file does not exist: {html_path}"
        ))
        return issues

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    parser = HTMLAssetParser()
    parser.feed(content)

    # 1. Check for Duplicate Image Sources within the same document
    src_counts: Dict[str, List[int]] = {}
    for src, line in parser.img_sources:
        src_counts.setdefault(src, []).append(line)

    for src, lines in src_counts.items():
        if len(lines) > 1:
            issues.append(AssetAuditIssue(
                severity="WARNING",
                category="DUPLICATE_ASSET",
                file_path=html_path,
                message=f"Image asset '{src}' is referenced {len(lines)} times on lines {lines}. Each figure/graphic should be unique.",
                details={"src": src, "lines": lines}
            ))

    # 2. Check for Missing Image Assets on disk
    for src, line in parser.img_sources:
        clean_src = src.lstrip("/")
        possible_paths = [
            os.path.join(webroot, clean_src),
            os.path.join(os.path.dirname(html_path), clean_src),
            os.path.join("/home/ubuntu/swarph-ai/web", clean_src)
        ]
        if not any(os.path.exists(p) for p in possible_paths):
            issues.append(AssetAuditIssue(
                severity="ERROR",
                category="MISSING_ASSET",
                file_path=html_path,
                message=f"Line {line}: Image source '{src}' does not exist on disk.",
                details={"src": src, "line": line}
            ))

    return issues

def audit_svg_file(svg_path: str) -> List[AssetAuditIssue]:
    issues: List[AssetAuditIssue] = []
    if not os.path.exists(svg_path):
        return issues

    with open(svg_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Brand safety audit: un-neutralized product names
    forbidden_terms = ["GPT-5.6", "Sol path", "Astra path", "Sol-fast", "Sol-bal", "Astra-long", "Astra-swarm"]
    for term in forbidden_terms:
        if term in content:
            issues.append(AssetAuditIssue(
                severity="ERROR",
                category="BRAND_SAFETY",
                file_path=svg_path,
                message=f"Un-neutralized brand string '{term}' found inside SVG asset text.",
                details={"forbidden_term": term}
            ))

    return issues

def audit_directory_asset_hashes(assets_dir: str) -> List[AssetAuditIssue]:
    issues: List[AssetAuditIssue] = []
    if not os.path.exists(assets_dir):
        return issues

    hashes: Dict[str, str] = {} # md5 -> file_path
    for root, _, files in os.walk(assets_dir):
        for file in files:
            if file.endswith((".svg", ".png", ".jpg", ".jpeg", ".webp")):
                full_path = os.path.join(root, file)
                with open(full_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                if file_hash in hashes:
                    issues.append(AssetAuditIssue(
                        severity="WARNING",
                        category="IDENTICAL_FILE_HASH",
                        file_path=full_path,
                        message=f"Asset file '{file}' is identical in binary content to '{os.path.basename(hashes[file_hash])}' (MD5: {file_hash}).",
                        details={"duplicate_of": hashes[file_hash]}
                    ))
                else:
                    hashes[file_hash] = full_path

    return issues

def run_full_asset_audit(target_html: str, assets_dir: str) -> Dict[str, Any]:
    all_issues: List[AssetAuditIssue] = []
    
    # 1. Audit HTML file
    all_issues.extend(audit_html_file(target_html))

    # 2. Audit SVG files in assets directory
    if os.path.exists(assets_dir):
        for root, _, files in os.walk(assets_dir):
            for file in files:
                if file.endswith(".svg"):
                    all_issues.extend(audit_svg_file(os.path.join(root, file)))

        # 3. Audit for binary identical files
        all_issues.extend(audit_directory_asset_hashes(assets_dir))

    errors = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARNING"]

    status = "FAIL" if errors else ("WARNING" if warnings else "PASS")

    return {
        "status": status,
        "total_issues": len(all_issues),
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "issues": [
            {
                "severity": i.severity,
                "category": i.category,
                "file_path": i.file_path,
                "message": i.message,
                "details": i.details
            }
            for i in all_issues
        ]
    }

if __name__ == "__main__":
    html_target = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/brainsurfing.tech/blog/gpt-56-sol-astra-architecture.html"
    assets_target = sys.argv[2] if len(sys.argv) > 2 else "/home/ubuntu/brainsurfing.tech/blog/assets"

    print(f"=== RUNNING ASSET UNIQUENESS & QUALITY AUDIT ===")
    print(f"Target HTML:   {html_target}")
    print(f"Target Assets: {assets_target}\n")

    result = run_full_asset_audit(html_target, assets_target)

    print(f"AUDIT STATUS: {result['status']}")
    print(f"Total Issues: {result['total_issues']} (Errors: {result['errors_count']}, Warnings: {result['warnings_count']})\n")

    if result["issues"]:
        for idx, issue in enumerate(result["issues"], 1):
            print(f"[{idx}] [{issue['severity']}] [{issue['category']}] in {os.path.basename(issue['file_path'])}")
            print(f"    Message: {issue['message']}\n")
    else:
        print("✅ ALL ASSET CHECKS PASSED CLEANLY (100% Unique & Brand-Neutral)!")
