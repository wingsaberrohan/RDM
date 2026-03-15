"""Start/stop aria2c daemon, health checks, and RPC client wrapper."""

import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

import aria2p

# Default RPC port
DEFAULT_RPC_PORT = 6800
# Directory under user home for RDM data (and optional bundled aria2)
RDM_DIR = Path.home() / ".rdm"
ARIA2_DIR = RDM_DIR / "aria2"


def find_aria2c() -> Optional[Path]:
    """Return path to aria2c executable: PATH first, then RDM aria2 dir."""
    exe = "aria2c.exe" if platform.system() == "Windows" else "aria2c"
    in_path = shutil.which("aria2c") or shutil.which("aria2c.exe")
    if in_path:
        return Path(in_path)
    local = ARIA2_DIR / exe
    if local.exists():
        return local
    return None


def ensure_aria2_dir() -> Path:
    """Ensure RDM aria2 directory exists. Caller may put aria2c binary here."""
    ARIA2_DIR.mkdir(parents=True, exist_ok=True)
    return ARIA2_DIR


class Aria2Manager:
    """Manages aria2c daemon process and provides an aria2p API client."""

    def __init__(self, rpc_port: int = DEFAULT_RPC_PORT):
        self._rpc_port = rpc_port
        self._process: Optional[subprocess.Popen] = None
        self._api: Optional[aria2p.API] = None

    @property
    def rpc_port(self) -> int:
        return self._rpc_port

    def is_running(self) -> bool:
        """Return True if our managed process is still running."""
        return self._process is not None and self._process.poll() is None

    def start(self) -> bool:
        """Start aria2c daemon. Prefer aria2c from PATH or RDM dir. Return True on success."""
        exe_path = find_aria2c()
        if not exe_path:
            return False
        cmd = [
            str(exe_path),
            f"--enable-rpc=true",
            f"--rpc-listen-port={self._rpc_port}",
            "--rpc-listen-all=false",
            "--file-allocation=none",
            "--continue=true",
        ]
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if platform.system() == "Windows" else 0,
            )
        except Exception:
            self._process = None
            return False
        # Wait for RPC to be ready
        for _ in range(50):
            time.sleep(0.1)
            if self._check_rpc():
                return True
        self.stop()
        return False

    def _check_rpc(self) -> bool:
        """Return True if RPC responds."""
        try:
            api = aria2p.API(aria2p.Client(port=self._rpc_port))
            api.get_version()
            return True
        except Exception:
            return False

    def stop(self) -> None:
        """Stop the aria2c process we started."""
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None
        self._api = None

    def get_api(self) -> Optional[aria2p.API]:
        """Return aria2p API instance. Starts daemon if not running and aria2c is available."""
        if self._api is not None:
            return self._api
        if self.is_running():
            self._api = aria2p.API(aria2p.Client(port=self._rpc_port))
            return self._api
        if self.start():
            self._api = aria2p.API(aria2p.Client(port=self._rpc_port))
            return self._api
        return None

    def health_check(self) -> bool:
        """Return True if we can talk to aria2 (either our process or an existing daemon)."""
        try:
            api = aria2p.API(aria2p.Client(port=self._rpc_port))
            api.get_version()
            if self._api is None:
                self._api = api
            return True
        except Exception:
            return False
