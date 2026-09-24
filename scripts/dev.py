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

The database is PostgreSQL (docs/adr/0004-database.md). Before migrating, a
task checks the local cluster and starts it if it is down; it never stops it.
Set PGSQL_HOME for an install other than ~/Binaries/pgsql. Under CI, or where
no local install exists, the check is skipped and the database must already be
accepting connections.
"""
import os
import shutil
import subprocess
import sys
import time
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
LINT_TARGETS = ["accounts", "shop", "mysite", "scripts", "tests"]

# Standalone executables, not Python requirements, so they are looked up rather
# than installed: first on PATH, then where this machine's tooling lives
# (~/Binaries/<dir>, alongside pgsql and node). Not part of `lint`, because CI's
# lint job has none of them.
WORKFLOW_TOOLS = {
    "actionlint": "actionlint",
    "shellcheck": "shellcheck",
    "pyflakes": "pyflakes/Scripts",
}

# Local PostgreSQL cluster that ensure_cluster() may start.
PGSQL_HOME = Path(os.getenv("PGSQL_HOME", Path.home() / "Binaries" / "pgsql"))

# pg_isready exit codes. Branch on these, never on the message: this cluster's
# output is localised, so the text differs by machine locale.
PG_READY, PG_STARTING, PG_DOWN = 0, 1, 2

CLUSTER_START_TIMEOUT = 30  # seconds, matching the night-run preflight

# Coverage over the application packages only -- see docs/adr/0005-testing.md.
# Gated since 2026-09-17: the target ADR 0005 left open is 95%, a little under
# the 99% the suite reaches, so an untested helper fails the run while a line
# or two of slack does not. Raising it is a decision; lowering it to make a
# run pass is not (docs/ai/night-2026-09-17/decisions.md D18).
#
# Applies to `dev.py test`, which runs every suite -- and so to CI, which runs
# that task. A single suite (`test:unit`, say) is not measured against it: its
# coverage of the whole application is not a meaningful number, and narrowing
# the full task (`dev.py test -- -k something`) fails on coverage for the same
# reason. Narrow with test:unit/test:int/test:e2e instead. Switching the gate
# off from the command line (`-- --no-cov`) is for looking at a failure, never
# what "dev.py test passed" means.
# coverage rounds the total before comparing (precision 0), so 94.6% passes a
# floor of 95 and 94.5% does not.
COVERAGE_FLOOR = 95
COV_ARGS = [
    "--cov=accounts", "--cov=shop", "--cov=mysite", "--cov-report=term-missing",
    f"--cov-fail-under={COVERAGE_FLOOR}",
]


def run(*args):
    """Run a Python command from the project root, echoing it first."""
    print(f"\n$ python {' '.join(args)}", flush=True)
    return subprocess.run([sys.executable, *args], cwd=BASE_DIR).returncode


def _pg_exe(name):
    exe = PGSQL_HOME / "bin" / (name + (".exe" if os.name == "nt" else ""))
    return exe if exe.exists() else None


def _pg_isready(exe):
    # Same probe as the night-run preflight: localhost:5432, as .env.example's
    # DATABASE_URL points at.
    return subprocess.run(
        [str(exe), "-h", "localhost", "-p", "5432"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode


def ensure_cluster():
    """Start the local cluster if it is down, so a task does not fail on it.

    Skipped under CI, whose database is a service container already healthy by
    the time any step runs, and wherever PGSQL_HOME holds no install -- there
    is nothing here to start, and migrate reports a missing database itself.

    Anything other than "down" or "starting" (exit 3, a bad invocation) is also
    left to migrate to report rather than guessed at here.
    """
    if os.environ.get("CI"):
        return 0
    isready, pg_ctl = _pg_exe("pg_isready"), _pg_exe("pg_ctl")
    if isready is None or pg_ctl is None:
        return 0

    state = _pg_isready(isready)
    if state not in (PG_STARTING, PG_DOWN):
        return 0

    if state == PG_DOWN:
        # Said aloud, not done quietly: an unattended run must be able to see
        # in its output that the cluster had gone down mid-run.
        print(f"dev.py: PostgreSQL cluster at {PGSQL_HOME} is down -- starting it.", flush=True)
        # Detached, or the server is a child of this shell and dies with it --
        # after every short-lived shell an agent opens, for instance.
        # Numeric, because the subprocess constants exist only on Windows and
        # CI lints on Linux.
        if os.name == "nt":
            detached_process, create_new_process_group = 0x00000008, 0x00000200
            detach = {"creationflags": detached_process | create_new_process_group}
        else:
            detach = {"start_new_session": True}
        subprocess.Popen(  # pylint: disable=consider-using-with
            [str(pg_ctl), "start", "-D", str(PGSQL_HOME / "data"),
             "-l", str(PGSQL_HOME / "server.log")],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, **detach,
        )

    deadline = time.monotonic() + CLUSTER_START_TIMEOUT
    while time.monotonic() < deadline:
        if _pg_isready(isready) == PG_READY:
            return 0
        time.sleep(1)
    print(
        f"dev.py: cluster not accepting connections after {CLUSTER_START_TIMEOUT}s. "
        f"See {PGSQL_HOME / 'server.log'}."
    )
    return 1


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
        code = ensure_cluster() or prepare()
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
