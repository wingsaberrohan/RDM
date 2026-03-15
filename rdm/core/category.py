"""File category management: auto-categorize by extension, custom categories with save paths."""

from pathlib import Path
from typing import Dict, List, Optional

from rdm.utils.file_utils import get_extension

# Built-in categories and their file extensions
DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".txt", ".rtf", ".tex", ".md"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg"],
    "Music": [".mp3", ".flac", ".wav", ".aac", ".ogg", ".wma", ".m4a", ".opus"],
    "Programs": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".apk", ".appimage", ".bat", ".sh"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif"],
    "General": [],
}

# Category -> default save path (optional; overridden by user settings)
_category_paths: Dict[str, Path] = {}


def get_category_for_filename(filename: str) -> str:
    """Return category name for a filename based on extension. Returns 'General' if no match."""
    ext = get_extension(filename)
    if not ext:
        return "General"
    for category, exts in DEFAULT_CATEGORIES.items():
        if ext.lower() in [e.lower() for e in exts]:
            return category
    return "General"


def get_all_categories() -> List[str]:
    """Return list of built-in category names."""
    return list(DEFAULT_CATEGORIES.keys())


def get_save_path_for_category(category: str) -> Optional[Path]:
    """Return custom save path for category if set, else None."""
    return _category_paths.get(category)


def set_save_path_for_category(category: str, path: Optional[Path]) -> None:
    """Set custom save path for a category."""
    if path is None:
        _category_paths.pop(category, None)
    else:
        _category_paths[category] = Path(path)


def get_download_dir_for_category(category: str, base_downloads: Path) -> Path:
    """Return the directory to use for a category: custom path or base_downloads/Category."""
    custom = get_save_path_for_category(category)
    if custom is not None and custom.is_dir():
        return custom
    return base_downloads / category.replace(" ", "_")
