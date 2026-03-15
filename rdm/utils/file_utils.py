"""File type detection and size formatting."""

from pathlib import Path


def format_size(num_bytes: int | None) -> str:
    """Format byte count as human-readable string (e.g. 1.5 MB)."""
    if num_bytes is None or num_bytes < 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}".replace(".0 ", " ")
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


def get_extension(path_or_name: str) -> str:
    """Return lowercase file extension including the dot, or empty string."""
    p = Path(path_or_name)
    ext = p.suffix
    return ext.lower() if ext else ""
