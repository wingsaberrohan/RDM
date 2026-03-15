"""Data models for download records (history)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DownloadRecord:
    """One row in download history."""

    id: Optional[int]
    url: str
    filename: str
    size: int
    status: str
    category: str
    date: str
    path: str
    gid: str = ""

    def to_row(self) -> tuple:
        return (
            self.id,
            self.url,
            self.filename,
            self.size,
            self.status,
            self.category,
            self.date,
            self.path,
            self.gid,
        )

    @classmethod
    def from_row(cls, row: tuple) -> "DownloadRecord":
        return cls(
            id=row[0],
            url=row[1],
            filename=row[2],
            size=row[3],
            status=row[4],
            category=row[5],
            date=row[6],
            path=row[7],
            gid=row[8] if len(row) > 8 else "",
        )
