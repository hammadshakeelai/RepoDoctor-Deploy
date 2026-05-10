"""
Shared tools that agents can use to interact with repositories.
These are registered as @function_tool for the OpenAI Agents SDK.
"""

import os
import json
import shutil
import tempfile
import re
from pathlib import Path
from agents import function_tool


REPO_TEMP_DIR = os.path.join(tempfile.gettempdir(), "repodoctor_repos")


@function_tool
def clone_repo(github_url: str) -> str:
    """Clone a GitHub repository to a temporary directory and return the local path.
    
    Args:
        github_url: The full GitHub URL (e.g., https://github.com/user/repo)
    """
    import git

    # Clean URL
    github_url = github_url.strip().rstrip("/")
    if github_url.endswith(".git"):
        repo_name = github_url.split("/")[-1][:-4]
    else:
        repo_name = github_url.split("/")[-1]

    # Create temp directory
    os.makedirs(REPO_TEMP_DIR, exist_ok=True)
    repo_path = os.path.join(REPO_TEMP_DIR, repo_name)

    # Remove existing clone if any
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)

    # Clone (shallow for speed)
    git.Repo.clone_from(github_url, repo_path, depth=1)

    return repo_path


@function_tool
def get_file_tree(repo_path: str, max_depth: int = 4) -> str:
    """Get the directory structure of a repository as a JSON tree.
    
    Args:
        repo_path: Local path to the cloned repository
        max_depth: Maximum depth to traverse (default 4)
    """
    def _build_tree(path: Path, current_depth: int = 0) -> dict:
        if current_depth > max_depth:
            return {"name": path.name, "type": "directory", "children": ["..."]}

        result = {"name": path.name, "type": "directory", "children": []}

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return result

        skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv",
                     "dist", "build", ".next", ".cache", "vendor", ".tox", "egg-info"}

        for item in items:
            if item.name.startswith(".") and item.name not in (".env.example", ".gitignore"):
                if item.is_dir():
                    continue
            if item.is_dir():
                if item.name in skip_dirs or item.name.endswith(".egg-info"):
                    continue
                result["children"].append(_build_tree(item, current_depth + 1))
            else:
                size = item.stat().st_size
                result["children"].append({
                    "name": item.name,
                    "type": "file",
                    "size": size,
                    "extension": item.suffix
                })

        return result

    tree = _build_tree(Path(repo_path))
    return json.dumps(tree, indent=2)


@function_tool
def read_file(repo_path: str, file_path: str) -> str:
    """Read the contents of a specific file in the repository.
    
    Args:
        repo_path: Local path to the cloned repository
        file_path: Relative path to the file within the repo
    """
    full_path = os.path.join(repo_path, file_path)
    if not os.path.exists(full_path):
        return f"Error: File '{file_path}' not found."

    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Truncate very large files
        if len(content) > 15000:
            content = content[:15000] + "\n\n... [TRUNCATED — file too large] ..."

        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


@function_tool
def analyze_dependencies(repo_path: str) -> str:
    """Analyze the project's dependency files (package.json, requirements.txt, go.mod, etc.)
    
    Args:
        repo_path: Local path to the cloned repository
    """
    dep_files = {
        "package.json": "Node.js / JavaScript",
        "requirements.txt": "Python",
        "Pipfile": "Python (Pipenv)",
        "pyproject.toml": "Python (Poetry/PEP 517)",
        "setup.py": "Python (setuptools)",
        "go.mod": "Go",
        "Cargo.toml": "Rust",
        "Gemfile": "Ruby",
        "pom.xml": "Java (Maven)",
        "build.gradle": "Java/Kotlin (Gradle)",
        "composer.json": "PHP",
    }

    results = {}
    for filename, lang in dep_files.items():
        filepath = os.path.join(repo_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                results[filename] = {
                    "language": lang,
                    "content": content[:5000]
                }
            except Exception:
                pass

    if not results:
        return json.dumps({"message": "No recognized dependency files found."})

    return json.dumps(results, indent=2)


@function_tool
def count_lines_by_language(repo_path: str) -> str:
    """Count lines of code grouped by programming language.
    
    Args:
        repo_path: Local path to the cloned repository
    """
    ext_to_lang = {
        ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (React)",
        ".ts": "TypeScript", ".tsx": "TypeScript (React)", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
        ".c": "C", ".cpp": "C++", ".h": "C/C++ Header",
        ".cs": "C#", ".swift": "Swift", ".kt": "Kotlin",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
        ".sql": "SQL", ".sh": "Shell", ".yml": "YAML", ".yaml": "YAML",
        ".json": "JSON", ".md": "Markdown", ".toml": "TOML",
    }

    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv",
                 "dist", "build", ".next", "vendor"}

    counts = {}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            lang = ext_to_lang.get(ext)
            if lang:
                try:
                    fpath = os.path.join(root, fname)
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        line_count = sum(1 for _ in f)
                    counts[lang] = counts.get(lang, 0) + line_count
                except Exception:
                    pass

    sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
    return json.dumps(sorted_counts, indent=2)


@function_tool
def search_code(repo_path: str, pattern: str) -> str:
    """Search through code files for a regex pattern. Returns matching lines with file paths.
    
    Args:
        repo_path: Local path to the cloned repository
        pattern: Regex pattern to search for
    """
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv",
                 "dist", "build", ".next", "vendor"}
    code_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go",
                       ".rs", ".rb", ".php", ".c", ".cpp", ".h", ".cs",
                       ".swift", ".kt", ".html", ".css", ".sql", ".sh"}

    results = []
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return json.dumps({"error": f"Invalid regex pattern: {pattern}"})

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in code_extensions:
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, repo_path)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for line_num, line in enumerate(f, 1):
                        if compiled.search(line):
                            results.append({
                                "file": rel_path.replace("\\", "/"),
                                "line": line_num,
                                "content": line.strip()[:200]
                            })
                            if len(results) >= 50:
                                return json.dumps(results, indent=2)
            except Exception:
                pass

    return json.dumps(results, indent=2)
