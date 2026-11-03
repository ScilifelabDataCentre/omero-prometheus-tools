import os
from pathlib import Path

from prometheus_client import Gauge


class XfsQuotaMetrics(object):
    """Collect per-group XFS project quota metrics for an OMERO ManagedRepository."""

    def __init__(self, mount_point: str | Path, verbose: bool = False) -> None:
        self.mount_point = Path(mount_point)
        self.verbose = verbose
        self.groups: set[str] = set()
        self.group_used_gauge = Gauge(
            "omero_xfs_quota_used_bytes",
            "XFS project quota used space in bytes per group",
            ["group"],
        )
        self.group_limit_gauge = Gauge(
            "omero_xfs_quota_hard_limit_bytes",
            "XFS project quota hard limit in bytes per group",
            ["group"],
        )

    def update(self) -> None:
        """Scan ManagedRepository groups with os.statvfs and update Prometheus gauges."""
        repo_dir = self.mount_point / "ManagedRepository"
        if not repo_dir.is_dir():
            repo_dir = self.mount_point

        try:
            group_entries = list(repo_dir.iterdir())
        except OSError as exc:
            if self.verbose:
                print(f"Cannot scan {repo_dir}: {exc}")
            return

        prev_groups = self.groups
        self.groups = set()

        for group_entry in group_entries:
            if not group_entry.is_dir(
                follow_symlinks=False
            ) or group_entry.name.startswith("."):
                continue
            group = group_entry.name
            try:
                vfs = os.statvfs(group_entry)
            except OSError:
                continue

            limit_bytes = vfs.f_blocks * vfs.f_frsize
            used_bytes = (vfs.f_blocks - vfs.f_bfree) * vfs.f_frsize
            self.group_used_gauge.labels(group).set(used_bytes)
            self.group_limit_gauge.labels(group).set(limit_bytes)
            self.groups.add(group)
            if self.verbose:
                print(f"xfs_quota group={group}: used={used_bytes} limit={limit_bytes}")

        for rm_group in prev_groups.difference(self.groups):
            self.group_used_gauge.remove(rm_group)
            self.group_limit_gauge.remove(rm_group)
