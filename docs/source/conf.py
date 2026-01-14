# # -- HTML output (optional) -------------------------------------
import os
import sys

# -----------------------------------------------------------------------------
# 1. Project Information
# -----------------------------------------------------------------------------
project = "Syntasa CCD Template"
copyright = "2026, Syntasa"
author = "Syntasa"

extensions = [
    "sphinxcontrib.confluencebuilder",
    "sphinx.ext.autodoc",
    "sphinx_design",  # Required for the dropdowns
    "myst_parser",  # Required for Markdown support
]

confluence_publish = True
confluence_space_key = os.environ.get("CONFLUENCE_SPACE_KEY")
confluence_server_url = os.environ.get("CONFLUENCE_URL")
confluence_server_user = os.environ.get("CONFLUENCE_USERNAME")
confluence_api_token = os.environ.get("CONFLUENCE_API_KEY")
confluence_ask_password = False
parent_id = os.environ.get("CONFLUENCE_PARENT_PAGE_KEY")
if parent_id:
    confluence_parent_page = int(parent_id)


if not confluence_server_url:
    print(
        "ERROR: confluence_server_url is missing. Check your .env file or variable names."
    )

# -----------------------------------------------------------------------------
# 3. Debugging (Verify variables are loaded)
# -----------------------------------------------------------------------------
print(f"DEBUG: URL: {confluence_server_url}")
print(f"DEBUG: User: {confluence_server_user}")
# Don't print the full token, just check length
if confluence_api_token:
    print(f"DEBUG: Token loaded (length: {len(confluence_api_token)})")
else:
    print("DEBUG: Token is EMPTY/NONE")

# Force standard "Fixed Width" layout (Centers content like Screenshot 3)
confluence_full_width = True
# Optional: Keep page titles tidy
confluence_page_hierarchy = True
# Mapping 'collapse' container to Confluence 'expand' macro
confluence_adv_container_macro_map = {"expand": "expand"}

