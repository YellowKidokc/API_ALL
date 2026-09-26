"""Lean 4 structural declaration extractor."""

import re
from typing import Dict, List, Any


DECL_KEYWORDS = [
    "axiom",
    "def",
    "theorem",
    "lemma",
    "structure",
    "class",
    "instance",
    "inductive",
    "abbrev",
    "example"
]

# Regex pattern for declaration head
DECL_PATTERN = re.compile(
    r"^(?:(?:@[^\n]+\s*)*)?(?:(?:noncomputable|partial|protected|private|scoped)\s+)*("
    + "|".join(DECL_KEYWORDS)
    + r")\s+(?:(?:\((?:default|priority)[^)]*\)\s*)*)?([A-Za-z0-9_.'«»]+)?",
    re.MULTILINE
)

IMPORT_PATTERN = re.compile(r"^import\s+([A-Za-z0-9_.'«»]+)", re.MULTILINE)
NAMESPACE_OPEN_PATTERN = re.compile(r"^namespace\s+([A-Za-z0-9_.'«»]+)", re.MULTILINE)
NAMESPACE_END_PATTERN = re.compile(r"^end(?:\s+([A-Za-z0-9_.'«»]+))?", re.MULTILINE)


class LeanExtractor:
    """Extract declarations, namespaces, signatures, and proofs from Lean 4 source."""

    @staticmethod
    def extract_imports(text: str) -> List[str]:
        return [m.group(1).strip("«»") for m in IMPORT_PATTERN.finditer(text)]

    @classmethod
    def extract_declarations(cls, text: str, rel_path: str = "") -> List[Dict[str, Any]]:
        lines = text.splitlines(keepends=True)
        imports = cls.extract_imports(text)

        # Track namespace stack line by line
        namespace_stack: List[str] = []
        declarations: List[Dict[str, Any]] = []

        i = 0
        total_lines = len(lines)

        while i < total_lines:
            line = lines[i]
            stripped = line.strip()

            # Skip pure comments or docstrings in loop head
            if stripped.startswith("/-") or stripped.startswith("--"):
                i += 1
                continue

            # Check namespace open
            ns_open = NAMESPACE_OPEN_PATTERN.match(stripped)
            if ns_open:
                ns_name = ns_open.group(1).strip("«»")
                namespace_stack.append(ns_name)
                i += 1
                continue

            # Check namespace end
            ns_end = NAMESPACE_END_PATTERN.match(stripped)
            if ns_end:
                if namespace_stack:
                    namespace_stack.pop()
                i += 1
                continue

            # Check declaration start
            decl_match = DECL_PATTERN.match(line)
            if decl_match:
                kind = decl_match.group(1)
                raw_name = decl_match.group(2) or ("anonymous_instance" if kind == "instance" else "unnamed_example")
                clean_name = raw_name.strip("«»")

                current_ns = ".".join(namespace_stack)
                fq_name = f"{current_ns}.{clean_name}" if current_ns else clean_name

                start_line = i + 1

                # Gather statement and proof body
                block_lines = [line]
                j = i + 1

                # Continue gathering lines until next declaration, namespace, or EOF
                while j < total_lines:
                    next_line = lines[j]
                    next_stripped = next_line.strip()

                    # Stop if next line is a new top-level declaration or namespace
                    if (DECL_PATTERN.match(next_line) or
                        NAMESPACE_OPEN_PATTERN.match(next_stripped) or
                        NAMESPACE_END_PATTERN.match(next_stripped)):
                        break

                    block_lines.append(next_line)
                    j += 1

                end_line = j
                full_block = "".join(block_lines)

                # Split statement and proof
                if ":=" in full_block:
                    stmt_part, proof_part = full_block.split(":=", 1)
                    formal_stmt = stmt_part.strip()
                    proof_script = proof_part.strip()
                else:
                    formal_stmt = full_block.strip()
                    proof_script = ""

                # Extract binders: (x : T), {x : T}, [x : T]
                binders = re.findall(r"[\(\[\{][^\)\]\}]+[\)\]\}]", formal_stmt)
                variables = [b.strip() for b in binders]

                # Extract return type if ':' present after binders
                types = []
                if ":" in formal_stmt:
                    type_part = formal_stmt.rsplit(":", 1)[1].strip()
                    if type_part:
                        types.append(type_part)

                declarations.append({
                    "declaration_kind": kind,
                    "declaration_name": clean_name,
                    "namespace": current_ns,
                    "fully_qualified_name": fq_name,
                    "formal_statement": formal_stmt,
                    "proof_script": proof_script,
                    "variables": variables,
                    "types": types,
                    "imports": imports,
                    "start_line": start_line,
                    "end_line": end_line
                })

                i = j
                continue

            i += 1

        return declarations
