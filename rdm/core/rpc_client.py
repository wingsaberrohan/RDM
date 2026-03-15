"""Thin wrapper over aria2p for RDM: add, pause, resume, remove, list."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import aria2p

from .aria2_manager import Aria2Manager


def _options(
    dir_path: Optional[Path] = None,
    out: Optional[str] = None,
    split: int = 8,
    max_connection_per_server: int = 8,
) -> Dict[str, Any]:
    opts: Dict[str, Any] = {
        "split": str(split),
        "max-connection-per-server": str(max_connection_per_server),
    }
    if dir_path is not None:
        opts["dir"] = str(dir_path.resolve())
    if out is not None:
        opts["out"] = out
    return opts


class RpcClient:
    """Wrapper around aria2p API for RDM. Requires Aria2Manager with get_api()."""

    def __init__(self, aria2_manager: Aria2Manager):
        self._manager = aria2_manager

    def _api(self) -> aria2p.API:
        api = self._manager.get_api()
        if api is None:
            raise RuntimeError("aria2 is not available. Install aria2 and ensure it is on PATH or in ~/.rdm/aria2/")
        return api

    def add_uri(
        self,
        uri: str,
        dir_path: Optional[Path] = None,
        out: Optional[str] = None,
        split: int = 8,
        max_connections: int = 8,
    ) -> Optional[aria2p.Download]:
        """Add a download. Returns Download or None on failure."""
        try:
            options = _options(
                dir_path=dir_path,
                out=out,
                split=split,
                max_connection_per_server=max_connections,
            )
            return self._api().add_uri([uri], options=options)
        except Exception:
            return None

    def pause(self, gid: str) -> bool:
        try:
            self._api().pause([gid])
            return True
        except Exception:
            return False

    def resume(self, gid: str) -> bool:
        try:
            self._api().resume([gid])
            return True
        except Exception:
            return False

    def remove(self, gid: str) -> bool:
        try:
            self._api().remove([gid])
            return True
        except Exception:
            return False

    def get_download(self, gid: str) -> Optional[aria2p.Download]:
        try:
            return self._api().get_download(gid)
        except Exception:
            return None

    def get_downloads(self, status: Optional[str] = None) -> List[aria2p.Download]:
        """Get downloads. status: 'active' | 'waiting' | 'paused' | 'error' | 'complete' | 'removed', or None for all."""
        try:
            if status is None:
                return self._api().get_downloads()
            return self._api().get_downloads(status)
        except Exception:
            return []

    def get_global_stat(self) -> Optional[dict]:
        try:
            return self._api().get_global_stat()
        except Exception:
            return None
