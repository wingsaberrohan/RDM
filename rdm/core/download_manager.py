"""Central download orchestration: add/pause/resume/cancel, progress polling, Qt signals."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from .aria2_manager import Aria2Manager
from .rpc_client import RpcClient


def _download_to_dict(d) -> Dict[str, Any]:
    """Convert aria2p Download to a flat dict for UI."""
    total = getattr(d, "total_length", None) or 0
    completed = getattr(d, "completed_length", None) or 0
    speed = getattr(d, "download_speed", None) or 0
    status = getattr(d, "status", "unknown")
    name = getattr(d, "name", None)
    if not name and getattr(d, "files", None) and len(d.files) > 0:
        path = getattr(d.files[0], "path", None)
        if path:
            name = Path(path).name
    if not name:
        name = "—"
    if total and total > 0 and speed > 0:
        eta_sec = (total - completed) / speed
    else:
        eta_sec = None
    uris = getattr(d, "uris", None) or []
    if not uris and getattr(d, "files", None):
        for f in d.files:
            if hasattr(f, "uris") and f.uris:
                uris = [u.get("uri", u) if isinstance(u, dict) else getattr(u, "uri", "") for u in f.uris]
                break
    return {
        "gid": getattr(d, "gid", ""),
        "name": name,
        "total_length": total,
        "completed_length": completed,
        "status": status,
        "download_speed": speed,
        "eta_seconds": eta_sec,
        "num_pieces": getattr(d, "num_pieces", 0),
        "connections": getattr(d, "connections", 0),
        "dir": str(getattr(d, "dir", "") or ""),
        "uris": uris if isinstance(uris, list) else [],
    }


class DownloadManager(QObject):
    """Orchestrates downloads via RpcClient and emits Qt signals for UI updates."""

    download_added = Signal(dict)
    download_removed = Signal(str)
    download_updated = Signal(str, dict)
    download_completed = Signal(str, dict)
    error_message = Signal(str)

    def __init__(self, aria2_manager: Aria2Manager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._aria2 = aria2_manager
        self._rpc = RpcClient(aria2_manager)
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_interval_ms = 500
        self._known_gids: set = set()
        self._prev_status: Dict[str, str] = {}

    def start_polling(self) -> None:
        """Start periodic poll of aria2 for progress updates."""
        if not self._poll_timer.isActive():
            self._poll_timer.start(self._poll_interval_ms)

    def stop_polling(self) -> None:
        self._poll_timer.stop()

    def _poll(self) -> None:
        try:
            downloads = self._rpc.get_downloads()
        except Exception as e:
            self.error_message.emit(str(e))
            return
        current = {d.gid for d in downloads}
        for d in downloads:
            data = _download_to_dict(d)
            if d.gid not in self._known_gids:
                self._known_gids.add(d.gid)
                self.download_added.emit(data)
            else:
                if self._prev_status.get(d.gid) != "complete" and data.get("status") == "complete":
                    self.download_completed.emit(d.gid, data)
                self._prev_status[d.gid] = data.get("status", "")
                self.download_updated.emit(d.gid, data)
        for gid in list(self._known_gids):
            if gid not in current:
                self._known_gids.discard(gid)
                self.download_removed.emit(gid)

    def add_download(
        self,
        url: str,
        save_dir: Optional[Path] = None,
        filename: Optional[str] = None,
        connections: int = 8,
    ) -> Optional[str]:
        """Add a download. Returns gid on success, None on failure."""
        try:
            download = self._rpc.add_uri(
                url,
                dir_path=save_dir,
                out=filename,
                max_connections=connections,
                split=connections,
            )
            if download is None:
                self.error_message.emit("Failed to add download.")
                return None
            self._known_gids.add(download.gid)
            self.start_polling()
            return download.gid
        except Exception as e:
            self.error_message.emit(str(e))
            return None

    def pause(self, gid: str) -> bool:
        return self._rpc.pause(gid)

    def resume(self, gid: str) -> bool:
        return self._rpc.resume(gid)

    def remove(self, gid: str) -> bool:
        return self._rpc.remove(gid)

    def get_downloads_snapshot(self) -> List[Dict[str, Any]]:
        """Return current list of download dicts (e.g. for initial table load)."""
        try:
            downloads = self._rpc.get_downloads()
            return [_download_to_dict(d) for d in downloads]
        except Exception:
            return []

    def is_idle(self) -> bool:
        """Return True if there are no active downloads."""
        try:
            return len(self._rpc.get_downloads("active")) == 0
        except Exception:
            return True
