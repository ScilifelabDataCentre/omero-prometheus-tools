#!/usr/bin/env python
import argparse
import os
import sys
from time import sleep, time

import omero.clients
from prometheus_client import Gauge, start_http_server

from . import CountMetrics, SessionMetrics, XfsQuotaMetrics


def connect(hostname: str, username: str, password: str):
    """Connect to OMERO server and return client."""
    client = omero.client(hostname)
    client.setAgent("prometheus-omero-tools")
    client.createSession(username, password)
    return client


def main() -> int:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="OMERO Prometheus monitoring tools")
    parser.add_argument("-c", "--config", action="append", help="Query configuration files")
    parser.add_argument(
        "-s",
        "--host",
        default="localhost",
        help="OMERO server hostname (default: localhost)",
    )
    parser.add_argument("-u", "--user", default="guest", help="OMERO username (default: guest)")
    parser.add_argument("-w", "--password", default="guest", help="OMERO password (default: guest)")
    parser.add_argument(
        "-l",
        "--listen",
        type=int,
        default=9449,
        help="Serve metrics on this port (default: 9449)",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=60,
        help="Interval (seconds) between updates (default: 60)",
    )
    parser.add_argument(
        "-q",
        "--quota-mount",
        default=os.environ.get("OMERO_QUOTA_MOUNT"),
        help="XFS mount path for quota metrics (or set OMERO_QUOTA_MOUNT)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose output")
    args = parser.parse_args()

    g_last_login = Gauge("omero_prometheus_tools_agent_login_time", "Time of last Prometheus agent login")

    try:
        client = connect(args.host, args.user, args.password)
        # Don't catch exception, exit on login failure so user knows
        g_last_login.set_to_current_time()
    except Exception as e:
        print(f"Failed to connect to OMERO server: {e}", file=sys.stderr)
        return 1

    try:
        # Start up the server to expose the metrics
        start_http_server(args.listen)
        print(f"Serving metrics on port {args.listen}")

        if args.config:
            counts = CountMetrics(client, args.config, args.verbose)
        else:
            counts = None

        if args.quota_mount:
            quotas = XfsQuotaMetrics(args.quota_mount, args.verbose)
        else:
            quotas = None

        sessions = SessionMetrics(client, verbose=args.verbose)

        while True:
            starttm = time()
            sessions.update()
            if counts:
                counts.update()
            if quotas:
                quotas.update()
            endtm = time()
            # HQL queries may take a long time
            sleep(max(args.interval + endtm - starttm, 0))

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        return 0
    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        return 1
    finally:
        try:
            client.closeSession()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
