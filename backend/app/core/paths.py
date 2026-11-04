from pathlib import Path
from backend.app.core.exceptions import PathTraversalError

def resolve_safe_path(root_dir: Path, relative_path: str) -> Path:
    """
    Safely resolves a relative path against a root directory, ensuring that
    no path traversal outside the root directory can occur.
    """
    root_resolved = root_dir.resolve()
    target_resolved = (root_resolved / relative_path).resolve()

    try:
        # Check if target_resolved is relative to root_resolved
        target_resolved.relative_to(root_resolved)
    except ValueError:
        raise PathTraversalError(relative_path)

    return target_resolved
