import os
import re
import sys
from pathlib import Path
import inspect
from bs4 import BeautifulSoup, Tag, NavigableString # type: ignore
from typing import Dict, Any, List, Optional, Set, Union, cast
# ==========================================
# 1. Parsing Logic
# ==========================================


def get_clean_source_code(tag: Tag)-> Optional[str]:
    """Extracts source code from .pdoc-code pre tag, removing line numbers."""
    pre_tag = tag.select_one(".pdoc-code pre")
    if not pre_tag:
        code_div = tag.select_one(".pdoc-code")
        if not code_div:
            return None
        pre_tag = code_div

    import copy

    code_copy = copy.copy(pre_tag)
    for lineno in code_copy.select(".linenos"):
        lineno.decompose()

    return code_copy.get_text()


def parse_single_member(tag: Tag, parent_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Extracts details from a Class or Function HTML tag."""
    name_tag = tag.select_one(".name")
    if not name_tag:
        return None
    name = name_tag.get_text(strip=True)

    attr_div = tag.select_one(".attr")
    # .get('class') returns list[str] | str | None
    classes: List[str] = []
    if attr_div:
        class_attr = attr_div.get('class')
        if isinstance(class_attr, list):
            classes = cast(List[str], class_attr)
        elif isinstance(class_attr, str):
            classes = [class_attr]
    member_type = "class" if "class" in classes or tag.name == 'section' else "function"
    
    

    sig_tag = tag.select_one(".signature")
    signature = sig_tag.get_text(" ", strip=True) if sig_tag else ""

    # Clean up signature spacing (Collapse newlines into single line)
    signature = signature.replace("\n", " ").replace("  ", " ")
    signature = signature.replace(" ,", ",").replace(" :", ":")
    signature = signature.replace("( ", "(").replace(" )", ")")
    signature = re.sub(r"\s*->\s*", " -> ", signature)
    signature = re.sub(r"\s*=\s*", "=", signature)

    if member_type == "class":
        bases = tag.select_one(".base")
        base_text = f"({bases.get_text(strip=True)})" if bases else ""
        definition = f"class {name}{base_text}"
    else:
        definition = f"def {name}{signature}"

    return {
        "name": name,
        "type": member_type,
        "definition": definition,
        "doc_html": tag.select_one(".docstring"),
        "source": get_clean_source_code(tag),
    }


def parse_html_to_structure(html_content: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html_content, "html.parser")
    data: Dict[str, Any] = {"title": "", "module_doc": "", "members": []}

    title_tag = soup.select_one(".modulename")
    if title_tag:
        data["title"] = title_tag.get_text(strip=True)

    module_info = soup.select_one("section.module-info .docstring")
    if module_info:
        data["module_doc"] = module_info

    for section in soup.select("section[id]"):
        member = parse_single_member(section)
        if member:
            data["members"].append(member)
            for method_div in section.select(".classattr > .attr.function"):
                method_wrapper = method_div.find_parent("div", class_="classattr")
                if method_wrapper:
                    sub = parse_single_member(
                        method_wrapper, parent_name=member["name"]
                    )
                    if sub:
                        data["members"].append(sub)
    return data


# ==========================================
# 2. Text Formatting (Visual Strategy)
# ==========================================


def html_to_rst_text(tag: Any) -> str:
    """
    Converts HTML to RST text.
    Uses simple formatting to avoid Sphinx directive errors.
    """
    if not tag:
        return ""
    blocks = []

    def clean_node(t: str) -> str:
        return t.replace("\n", " ").strip()

    for child in tag.children:
        if isinstance(child, NavigableString):
            text = clean_node(str(child))
            if text:
                blocks.append(text)

        elif child.name == "p":
            p_text = child.get_text(" ", strip=True)
            if p_text:
                blocks.append(p_text)

        elif child.name == "pre":
            # Format as simple code block
            code_block = [".. code-block:: python", ""]
            for cl in child.get_text().split("\n"):
                code_block.append(f"   {cl}")
            blocks.append("\n".join(code_block))

        elif child.name in ["ul", "ol"]:
            list_items = []
            for li in child.find_all("li"):
                # Ensure bullet is at start of line
                list_items.append(f"* {li.get_text(' ', strip=True)}")
            blocks.append("\n".join(list_items))

        elif child.name in ["h1", "h2", "h3", "h4"]:
            blocks.append(f"**{child.get_text(strip=True)}**")

    # Use double newlines to separate paragraphs cleanly
    return "\n\n".join(blocks)


def generate_confluence_rst(data: Dict[str, Any]) -> str:
    """
    Generates RST optimized for Confluence.
    Uses Bold Headers + Code Blocks instead of '.. class::' directives
    to prevent parsing errors with complex types.
    """
    out = []

   # 1. Page Title
    base_title = data["title"]
    title = f"{base_title} (Audiences)"

    # Confluence page title
    out.append(f":confluence_page_title: {title}")
    out.append("")

    out.append(title)
    out.append("=" * len(title))
    out.append("")
    # Standard module directive for index, but no content generation
    out.append(f".. module:: {title}")
    out.append("   :no-index:")
    out.append("")

    # 2. Module Docstring
    if data["module_doc"]:
        out.append(html_to_rst_text(data["module_doc"]))
        out.append("")

        header = "API Documentation"
        out.append(header)
        out.append("-" * len(header))
        out.append("")

    # 3. Members (Collecting blocks)
    member_blocks = []

    # 
    module_name = data["title"]  # e.g. "my_function.main"

    for member in data["members"]:
    # 🚫 Skip imported/template symbols
        if member.get("module") != module_name:
            continue
        block = []

        # --- A. Name (Bold Header) ---
        # This replaces ".. class:: Name"
        # It renders as bold text, aligned left.
        block.append(f"**{member['name']}**")
        block.append("")

        # --- B. Signature (Code Block) ---
        # This prevents "invalid option block" errors caused by complex signatures
        block.append(".. code-block:: python")
        block.append("")
        block.append(f"   {member['definition']}")
        block.append("")

        # --- C. Docstring ---
        if member["doc_html"]:
            doc_text = html_to_rst_text(member["doc_html"])
            # Format common headers
            for r in (
                ("Args:", "**Args:**"),
                ("Returns:", "**Returns:**"),
                ("Raises:", "**Raises:**"),
                ("Examples:", "**Examples:**"),
            ):
                doc_text = doc_text.replace(*r)

            block.append(doc_text)
            block.append("")

        # --- D. View Source (Dropdown) ---
        if member["source"]:
            block.append(".. dropdown:: View Source")
            block.append("")
            block.append("   .. code-block:: python")
            block.append("")

            # Indent source code 3 spaces relative to code-block
            for s_line in member["source"].split("\n"):
                block.append(f"      {s_line}" if s_line.strip() else "")
            block.append("")

        member_blocks.append("\n".join(block))

    # Join members with a Transition Rule (----) in between
    # This prevents the "Document may not end with a transition" error
    if member_blocks:
        out.append("\n\n----\n\n".join(member_blocks))

    return "\n".join(out)

# def generate_confluence_rst(structure: dict, module_path: Path) -> str:
#     """
#     Generates RST for Confluence. If structure is empty, dynamically loads
#     the Python module to generate real function/class documentation.
#     """
#     # If no members, fall back to dynamic inspection
#     if not structure.get("members"):
#         # Load module dynamically
#         import importlib.util
#         import sys

#         module_name = module_path.stem
#         spec = importlib.util.spec_from_file_location(module_name, str(module_path))
#         module = importlib.util.module_from_spec(spec)
#         sys.modules[module_name] = module
#         spec.loader.exec_module(module)

#         # Build structure from module
#         members = []

#         # Module-level functions
#         for name, func in inspect.getmembers(module, inspect.isfunction):
#             members.append({
#                 "name": name,
#                 "definition": f"def {name}{inspect.signature(func)}: ...",
#                 "doc_html": func.__doc__ or "",
#                 "source": inspect.getsource(func)
#             })

#         # Classes and methods
#         for cls_name, cls in inspect.getmembers(module, inspect.isclass):
#             if cls.__module__ != module_name:
#                 continue
#             members.append({
#                 "name": f"Class: {cls_name}",
#                 "definition": "",
#                 "doc_html": cls.__doc__ or "",
#                 "source": ""
#             })
#             for meth_name, meth in inspect.getmembers(cls, inspect.isfunction):
#                 if meth.__qualname__.split(".")[0] != cls_name:
#                     continue
#                 members.append({
#                     "name": f"Method: {cls_name}.{meth_name}",
#                     "definition": f"def {meth_name}{inspect.signature(meth)}: ...",
#                     "doc_html": meth.__doc__ or "",
#                     "source": inspect.getsource(meth)
#                 })

#         structure["members"] = members
#         structure["title"] = module_name

#     # --- Now continue with existing RST generation logic ---
#     # (the rest of your original generate_confluence_rst function can remain unchanged)
#     out = []

#     # Page Title
#     base_title = structure["title"]
#     title = f"{base_title} (Audiences)"
#     out.append(f":confluence_page_title: {title}")
#     out.append("")
#     out.append(title)
#     out.append("=" * len(title))
#     out.append("")

#     if structure.get("module_doc"):
#         out.append(structure["module_doc"])
#         out.append("")

#     # Members
#     for member in structure["members"]:
#         out.append(f"**{member['name']}**\n")
#         out.append(".. code-block:: python\n")
#         out.append("")
#         out.append(f"   {member['definition']}\n")
#         if member.get("doc_html"):
#             out.append(member["doc_html"])
#             out.append("")
#         if member.get("source"):
#             out.append(".. dropdown:: View Source\n")
#             out.append(".. code-block:: python\n")
#             out.append("")
#             for line in member["source"].splitlines():
#                 out.append(f"   {line}" if line.strip() else "")
#             out.append("")

#     return "\n".join(out)


# ==========================================
# 3. Execution
# ==========================================


def generate_index_file(folder_path: Path, subfolders: List[str], files: List[Path]) -> None:
    """Generates sorted index.rst for folder navigation."""
    folder_name = (
        folder_path.name.replace("_", " ").title()
        if folder_path.name != "source"
        else "Lib Reference - Syntasa Audiences"
    )

    content = []
    content.append(folder_name)
    content.append("=" * len(folder_name))
    content.append("")
    content.append(".. toctree::")
    content.append("   :maxdepth: 2")
    content.append("   :caption: Contents")
    # content.append("   :glob:")
    content.append("")

    if (folder_path / "readme.md").exists():
        content.append("   readme")

    for sub in sorted(subfolders):
        content.append(f"   /index")

    for path_obj in sorted(files):
        content.append(f"   {path_obj.stem}")

    index_path = folder_path / "index.rst"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))


def convert_recursive(input_dir: str, output_dir: str) -> None:
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    tree_map: Dict[Path, Dict[str, Any]] = {}

    # Modules to skip content generation for (prevents conflicts with folders)
    EXCLUDED_MODULES = {
        "syntasa_df",
        "syntasa_common",
        "syntasa_io",
        "syntasa_time",
        "syntasa_internal",
    }

    print(f"Scanning {input_path}...")

    for html_file in input_path.rglob("*.html"):
        if html_file.name == "index.html":
            continue

        rel_path = html_file.relative_to(input_path)
        # rst_filename = rel_path.with_suffix(".rst")
        rst_filename = Path(
            rel_path.stem + "_audiences"
            ).with_suffix(".rst")
        target_file = output_path / rst_filename
        target_parent = target_file.parent

        target_parent.mkdir(parents=True, exist_ok=True)

        # Build Tree Map
        if target_parent not in tree_map:
            tree_map[target_parent] = {"files": [], "folders": set()}

        # Register file for indexing
        if rst_filename.name != "index.rst":
            # Only add to file index if NOT excluded
            if html_file.stem not in EXCLUDED_MODULES:
                tree_map[target_parent]["files"].append(rst_filename.name)

            if target_parent != output_path:
                p = target_parent.parent
                if p not in tree_map:
                    tree_map[p] = {"files": [], "folders": set()}
                tree_map[p]["folders"].add(target_parent.name)

        if html_file.stem in EXCLUDED_MODULES:
            print(f"Skipping content generation for parent module: {html_file.stem}")
            continue

        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            structure = parse_html_to_structure(content)
            # if not structure["title"] and not structure["members"]:
            #     continue
            # if html_file.stem == "main":
            #     rst_output = generate_confluence_rst({}, Path("functions/my_function/main.py"))
            # else:
            #     structure = parse_html_to_structure(content)
            #     rst_output = generate_confluence_rst(structure, html_file)
            rst_output = generate_confluence_rst(structure)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(rst_output)
        except Exception as e:
            print(f"Failed to convert {html_file}: {e}")

    # Generate Indices
    for folder, folder_data in tree_map.items():
        files = [Path(f) for f in folder_data["files"]]
        folders = list(folder_data["folders"])
        generate_index_file(folder, folders, files)


if __name__ == "__main__":
    in_dir = sys.argv[1] if len(sys.argv) > 1 else "site"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "docs/source"
    convert_recursive(in_dir, out_dir)
