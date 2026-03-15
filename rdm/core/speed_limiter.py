"""Bandwidth throttling: global and per-download speed limits via aria2 RPC."""

from typing import Optional

from .rpc_client import RpcClient


def _kbps(value_kbps: int) -> str:
    """aria2 expects speed as string, e.g. '0' for unlimited or '1024' for 1024K."""
    return str(value_kbps) if value_kbps > 0 else "0"


class SpeedLimiter:
    """Apply global download speed limit via aria2 RPC. 0 = unlimited."""

    def __init__(self, rpc: RpcClient):
        self._rpc = rpc
        self._current_limit_kbps: int = 0

    def set_global_limit_kbps(self, kbps: int) -> bool:
        """Set overall download limit in KiB/s. 0 = unlimited. Returns True on success."""
        try:
            api = self._rpc._api()
            opts = {"max-overall-download-limit": _kbps(kbps)}
            if hasattr(api, "set_global_options"):
                api.set_global_options(opts)
            else:
                api.client.change_global_option(opts)
            self._current_limit_kbps = kbps
            return True
        except Exception:
            try:
                api.client.call("changeGlobalOption", opts)
                self._current_limit_kbps = kbps
                return True
            except Exception:
                return False

    def get_global_limit_kbps(self) -> int:
        return self._current_limit_kbps

    def set_download_limit_kbps(self, gid: str, kbps: int) -> bool:
        """Set per-download limit in KiB/s. 0 = unlimited."""
        try:
            api = self._rpc._api()
            opts = {"max-download-limit": _kbps(kbps)}
            if hasattr(api, "set_options"):
                api.set_options([gid], opts)
            else:
                api.client.change_option(gid, opts)
            return True
        except Exception:
            return False
