"""Project task runner.

    python scripts/dev.py run                 # dev server at 127.0.0.1:8000
    python scripts/dev.py test                # whole suite, with coverage
    python scripts/dev.py test:unit           # tests/unit only
    python scripts/dev.py test:int            # tests/integration only
    python scripts/dev.py test:e2e            # tests/e2e only
    python scripts/dev.py run -- 8080         # pass extra args through
    python scripts/dev.py test:unit -- -x -v

Every task generates and applies migrations first, so the database always
matches the models before the server starts or the tests run.

The database is PostgreSQL (docs/adr/0004-database.md) and must already be
accepting connections -- this runner no longer starts or stops the cluster.
"""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# pytest's exit code when a suite directory exists but holds no tests yet.
NO_TESTS_COLLECTED = 5

SUITES = {
    "test": "tests",
    "test:unit": "tests/unit",
    "test:int": "tests/integration",
    "test:e2e": "tests/e2e",
}

# 'test' runs everything, so collecting nothing there means the suite is gone,
# not merely unwritten. Only the per-suite tasks may legitimately be empty.
MAY_BE_EMPTY = set(SUITES) - {"test"}

TASKS = ["run", *SUITES]

# Coverage over the application packages only -- see docs/adr/0005-testing.md.
# Reported, not gated: ADR 0005 chose pytest-cov but agreed no threshold. Add
# --cov-fail-under here once there is a target to hold the suite to.
COV_ARGS = ["--cov=shop", "--cov=mysite", "--cov-report=term-missing"]


def run(*args):
    """Run a Python command from the project root, echoing it first."""
    print(f"\n$ python {' '.join(args)}", flush=True)
    return subprocess.run([sys.executable, *args], cwd=BASE_DIR).returncode


def prepare():
    """Bring the schema up to date before any task runs.

    Both steps are deliberate: makemigrations writes any model change that has
    no migration yet, and migrate applies it. A task that skipped either could
    run against a stale database.
    """
    code = run("manage.py", "makemigrations")
    if code:
        return code
    return run("manage.py", "migrate")


def pytest_suite(task, extra):
    # Full suite only. A per-suite run measures the whole application against a
    # fraction of the tests, so its number looks like a coverage regression.
    cov = COV_ARGS if task == "test" else []
    code = run("-m", "pytest", SUITES[task], *cov, *extra)
    if code == NO_TESTS_COLLECTED:
        if task in MAY_BE_EMPTY:
            print(f"({task}: {SUITES[task]}/ holds no tests yet - not a failure)")
            return 0
        # 'test' collecting nothing means the whole suite is missing.
        print(
            f"\n{task}: pytest collected no tests at all under {SUITES[task]}/.\n"
            "An empty suite is not a passing suite -- treating this as a failure."
        )
    return code


def main(argv):
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    tasks = argv[:argv.index("--")] if "--" in argv else argv

    if not tasks:
        print(__doc__)
        return 2

    # Reject unknown tasks before touching the database, so a typo cannot
    # generate migrations as a side effect of doing nothing else.
    for task in tasks:
        if task not in TASKS:
            print(f"Unknown task '{task}'. Available: {', '.join(TASKS)}")
            return 2

    code = prepare()
    if code:
        return code

    for task in tasks:
        if task == "run":
            code = run("manage.py", "runserver", *extra)
        else:
            code = pytest_suite(task, extra)
        if code:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
