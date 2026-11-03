import subprocess

from prometheus_client import Gauge


class XfsQuotaMetrics(object):
    """Collect per-user XFS quota metrics for an OMERO mount point."""

    def __init__(self, mount_point: str, verbose: bool = False) -> None:
        self.mount_point = mount_point
        self.verbose = verbose
        self.labelsets: set[tuple[str, str]] = set()
        labels = ["group", "user_id"]
        self.used_gauge = Gauge(
            "omero_xfs_quota_used_bytes",
            "XFS quota used space in bytes per group and user_id",
            labels,
        )
        self.soft_gauge = Gauge(
            "omero_xfs_quota_soft_limit_bytes",
            "XFS quota soft limit in bytes per group and user_id",
            labels,
        )
        self.hard_gauge = Gauge(
            "omero_xfs_quota_hard_limit_bytes",
            "XFS quota hard limit in bytes per group and user_id",
            labels,
        )

    @staticmethod
    def _parse_project_target(target: str) -> tuple[str, str]:
        """Split project target into (group, user_id) if delimited, else ('', target)."""
        for sep in ("/", ":"):
            if sep in target:
                group, user_id = target.split(sep, 1)
                return group, user_id
        return "", target

    def update(self) -> None:
        """Run xfs_quota report on mount_point and update Prometheus gauges."""
        cmd = ["xfs_quota", "-c", "report -p -b -N", self.mount_point]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            if self.verbose:
                print(f"xfs_quota failed on {self.mount_point}: {exc}")
            return

        prev_labelsets = self.labelsets
        self.labelsets = set()

        for line in proc.stdout.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            labelset = self._parse_project_target(parts[0])
            try:
                # xfs_quota reports blocks in 1 KiB units
                used_bytes = int(parts[1]) * 1024
                soft_bytes = int(parts[2]) * 1024
                hard_bytes = int(parts[3]) * 1024
            except ValueError:
                continue

            self.used_gauge.labels(*labelset).set(used_bytes)
            self.soft_gauge.labels(*labelset).set(soft_bytes)
            self.hard_gauge.labels(*labelset).set(hard_bytes)
            self.labelsets.add(labelset)
            if self.verbose:
                print(
                    f"xfs_quota {labelset}: used={used_bytes} soft={soft_bytes} hard={hard_bytes}"
                )

        for rm in prev_labelsets.difference(self.labelsets):
            self.used_gauge.remove(*rm)
            self.soft_gauge.remove(*rm)
            self.hard_gauge.remove(*rm)
