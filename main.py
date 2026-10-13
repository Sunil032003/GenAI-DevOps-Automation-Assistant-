"""
Forward Deployment Engineer (FDE) Autonomous Multi-Agent System
Main Production Entrypoint.
"""

import os
import sys

from cli import run_pipeline


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("  FORWARD DEPLOYMENT ENGINEER (FDE) MULTI-AGENT SYSTEM")
        print("=" * 60)
        print("\nUsage: python main.py <project_path> [--max-repairs N]")
        print("\nExamples:")
        print(r'  python main.py "C:\path\to\client_project"')
        print(r'  python main.py . --max-repairs 3')
        print("\nOr use the enhanced CLI:")
        print("  python cli.py --help")
        sys.exit(1)

    project_path = sys.argv[1]
    max_repairs = 3

    # Check for optional --max-repairs flag
    if "--max-repairs" in sys.argv:
        try:
            idx = sys.argv.index("--max-repairs")
            max_repairs = int(sys.argv[idx + 1])
        except (ValueError, IndexError):
            max_repairs = 3

    sys.exit(run_pipeline(project_path, max_repairs=max_repairs))


if __name__ == "__main__":
    main()