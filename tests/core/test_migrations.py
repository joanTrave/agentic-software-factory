import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_alembic_upgrade_head_then_downgrade_base_round_trips_cleanly():
    try:
        subprocess.run(["alembic", "upgrade", "head"], cwd=_REPO_ROOT, check=True)
        subprocess.run(["alembic", "downgrade", "base"], cwd=_REPO_ROOT, check=True)
    finally:
        # Leave the database back at head regardless of outcome so other tests in the
        # suite (which assume a fully migrated schema) are not affected by test order.
        subprocess.run(["alembic", "upgrade", "head"], cwd=_REPO_ROOT, check=True)
