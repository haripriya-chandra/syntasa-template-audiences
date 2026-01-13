# # -- HTML output (optional) -------------------------------------
import os
import sys


# -----------------------------------------------------------------------------
# 1. Load Environment Variables (Robust Path)
# -----------------------------------------------------------------------------
def load_env_manually(env_path):
    if not os.path.exists(env_path):
        print(f"ERROR: .env file not found at {env_path}")
        return

    print(f"DEBUG: Loading .env from: {env_path}")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.split("#", 1)[0].strip()
                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]
                os.environ[key] = val


conf_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(conf_dir, "../../"))
env_path = os.path.join(project_root, ".env")

load_env_manually(env_path)


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

