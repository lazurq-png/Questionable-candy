"""Project task runner.

    python scripts/dev.py run                 # dev server at 127.0.0.1:8000
    python scripts/dev.py lint                # pylint; errors fail, rest advisory
    python scripts/dev.py lint:workflows      # actionlint + shellcheck + pyflakes
    python scripts/dev.py test                # whole suite, with coverage
    python scripts/dev.py test:unit           # tests/unit only
    python scripts/dev.py test:int            # tests/integration only
    python scripts/dev.py test:e2e            # tests/e2e only
    python scripts/dev.py run -- 8080         # pass extra args through
    python scripts/dev.py test:unit -- -x -v

Every task generates and applies migrations first, so the database always
matches the models before the server starts or the tests run. The exceptions are
the `lint` tasks, which only read source and so must not require a running
database.

The database is PostgreSQL (docs/adr/0004-database.md) and must already be
accepting connections -- this runner no longer starts or stops the cluster.
"""
import os
import shutil
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

TASKS = ["run", "lint", "lint:workflows", *SUITES]

# Tasks that read source and never query. Paying for makemigrations/migrate
# would make lint unrunnable whenever the cluster is down -- precisely when a
# source-only check is still perfectly valid.
NO_DB_TASKS = {"lint", "lint:workflows"}

# Migrations are excluded by .pylintrc, not here.
LINT_TARGETS = ["shop", "mysite", "scripts", "tests"]

# Standalone executables, not Python requirements, so they are looked up rather
# than installed: first on PATH, then where this machine's tooling lives
# (~/Binaries/<dir>, alongside pgsql and node). Not part of `lint`, because CI's
# lint job has none of them.
WORKFLOW_TOOLS = {
    "actionlint": "actionlint",
    "shellcheck": "shellcheck",
    "pyflakes": "pyflakes/Scripts",
}

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


def lint(extra):
    """Errors fail the build; warnings, refactors and conventions only print.

    pylint's exit status is a bitfield, one bit per message class, so a plain
    run returns non-zero for a missing docstring. --fail-under=0 drops that
    score-based failure and --fail-on=E puts back the one that matters, which
    leaves a single pass that reports everything and fails on errors alone.

    Configuration -- the Django plugin, the settings module, the migration
    exclusion -- lives in .pylintrc so that a bare `pylint shop/` agrees with
    this task.
    """
    return run("-m", "pylint", "--fail-under=0", "--fail-on=E", *LINT_TARGETS, *extra)


def lint_workflows(extra):
    """actionlint over .github/workflows/, with shellcheck and pyflakes.

    actionlint checks the workflow schema and expressions; shellcheck checks
    the shell inside `run:` steps; pyflakes checks `shell: python` steps.
    Left to itself, actionlint *silently disables* either rule whose tool is
    not on PATH and still exits 0 -- a clean report that checked less than it
    appears to. So all three are resolved here, passed by explicit path, and a
    missing one fails the task instead of narrowing it.
    """
    binaries = Path.home() / "Binaries"
    search = os.pathsep.join(
        [os.environ.get("PATH", ""), *(str(binaries / d) for d in WORKFLOW_TOOLS.values())]
    )
    found = {name: shutil.which(name, path=search) for name in WORKFLOW_TOOLS}
    missing = [name for name, path in found.items() if path is None]
    if missing:
        print(
            f"lint:workflows: not found: {', '.join(missing)} "
            f"(looked on PATH and under {binaries}).\n"
            "Not running actionlint with rules missing -- that is not a pass."
        )
        return 2

    args = [
        found["actionlint"],
        f"-shellcheck={found['shellcheck']}",
        f"-pyflakes={found['pyflakes']}",
        *extra,
    ]
    print(f"\n$ {' '.join(args)}", flush=True)
    return subprocess.run(args, cwd=BASE_DIR).returncode


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

    if not all(task in NO_DB_TASKS for task in tasks):
        code = prepare()
        if code:
            return code

    for task in tasks:
        if task == "run":
            code = run("manage.py", "runserver", *extra)
        elif task == "lint":
            code = lint(extra)
        elif task == "lint:workflows":
            code = lint_workflows(extra)
        else:
            code = pytest_suite(task, extra)
        if code:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
