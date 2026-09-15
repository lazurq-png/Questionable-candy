"""Project task runner.

    python scripts/dev.py run                 # dev server at 127.0.0.1:8000
    python scripts/dev.py validate            # the full verification sequence
    python scripts/dev.py test                # whole suite
    python scripts/dev.py test:unit           # tests/unit only
    python scripts/dev.py test:integration    # tests/integration only
    python scripts/dev.py test:e2e            # tests/e2e only
    python scripts/dev.py migrations          # makemigrations only
    python scripts/dev.py migrations:check    # fail if migrations are missing
    python scripts/dev.py db:start            # start the local PostgreSQL cluster
    python scripts/dev.py db:stop             # stop it
    python scripts/dev.py db:status           # is it running?
    python scripts/dev.py run -- 8080         # pass extra args through
    python scripts/dev.py test:unit -- -x -v

'run' generates missing migrations and applies them before starting the server.
Test tasks only *check* for missing migrations -- they never write to the repo.

The database is PostgreSQL (docs/adr/0004-database.md). The db:* tasks drive a
local cluster; set PGSQL_HOME to point at a PostgreSQL install other than the
default below.
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
    "test:integration": "tests/integration",
    "test:e2e": "tests/e2e",
}

# 'test' runs everything, so collecting nothing there means the suite is gone,
# not merely unwritten. Only the per-suite tasks may legitimately be empty.
MAY_BE_EMPTY = set(SUITES) - {"test"}

# Local PostgreSQL cluster. Override with PGSQL_HOME for a different install.
PGSQL_HOME = Path(os.getenv("PGSQL_HOME", r"C:\Users\i221183\Binaries\pgsql"))

DB_READY_TIMEOUT = 20  # seconds to wait for the cluster to accept connections

# Coverage over the application packages only -- see docs/adr/0005-testing.md.
COV_ARGS = ["--cov=shop", "--cov=mysite", "--cov-report=term-missing"]


def run(*args):
    """Run a Python command from the project root, echoing it first."""
    print(f"\n$ python {' '.join(args)}", flush=True)
    return subprocess.run([sys.executable, *args], cwd=BASE_DIR).returncode


def makemigrations(check=False):
    args = ["manage.py", "makemigrations"]
    if check:
        args += ["--check", "--dry-run", "--noinput"]
    code = run(*args)
    if code and check:
        print("\nMissing migrations: run 'python scripts/dev.py migrations'.")
    return code


# --- PostgreSQL -----------------------------------------------------------

def _pg_tool(name):
    """Absolute path to a PostgreSQL binary, or None if this install lacks it."""
    exe = PGSQL_HOME / "bin" / (name + (".exe" if os.name == "nt" else ""))
    if exe.exists():
        return str(exe)
    found = shutil.which(name)  # fall back to a PostgreSQL that is on PATH
    if found:
        return found
    print(f"Could not find '{name}'. Looked in {PGSQL_HOME / 'bin'} and on PATH.")
    print("Set PGSQL_HOME to your PostgreSQL install directory.")
    return None


def _pg_ctl(*args, detached=False):
    exe = _pg_tool("pg_ctl")
    if exe is None:
        return 1
    cmd = [exe, "-D", str(PGSQL_HOME / "data"), *args]
    print(f"\n$ {' '.join(cmd)}", flush=True)
    if not detached:
        return subprocess.run(cmd).returncode

    # The server must outlive this process. Without detaching, the cluster is a
    # child of whatever shell started it and dies when that shell is closed.
    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        kwargs = {"creationflags": DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP}
    else:
        kwargs = {"start_new_session": True}
    subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )
    return 0


# 'pg_ctl status' exit codes. Branch on these and never on the message: pg_ctl
# output is localized, so the text differs by machine locale.
CLUSTER_RUNNING = 0
CLUSTER_STOPPED = 3
CLUSTER_NO_DATA_DIR = 4
CLUSTER_NO_TOOL = -1  # pg_ctl itself is missing; _pg_tool has already said so


def cluster_state():
    """Is *our* cluster running? Answers for PGSQL_HOME/data specifically.

    pg_isready cannot do this -- it has no -D option and probes whatever answers
    on the default host and port, which is not necessarily the cluster these
    tasks manage.
    """
    exe = _pg_tool("pg_ctl")
    if exe is None:
        return CLUSTER_NO_TOOL
    return subprocess.run(
        [exe, "-D", str(PGSQL_HOME / "data"), "status"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode


def _report_unusable_cluster(state):
    """Print why the cluster cannot be used, or return False if it can."""
    if state == CLUSTER_NO_TOOL:
        return True  # _pg_tool already printed where it looked
    if state == CLUSTER_NO_DATA_DIR:
        print(f"No PostgreSQL data directory at {PGSQL_HOME / 'data'}.")
        print("Set PGSQL_HOME to your PostgreSQL install directory.")
        return True
    return False


def db_is_ready():
    """Is something accepting connections on the default host/port?

    A different question from cluster_state(): a cluster can be running but not
    yet accepting connections, and something that is not our cluster at all can
    be answering on the port. Only meaningful alongside cluster_state().
    """
    exe = _pg_tool("pg_isready")
    if exe is None:
        return False
    return subprocess.run(
        [exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode == 0


def _warn_if_port_is_taken_by_another_server():
    """Report the case that used to pass silently as success.

    If our cluster is down but something answers on the port, starting is
    pointless and, worse, Django would connect to that other server instead --
    DATABASE_URL names a host and port, not a data directory.
    """
    if db_is_ready():
        print(
            "\nAnother PostgreSQL is already answering on the default port, but it is\n"
            f"NOT the cluster at {PGSQL_HOME / 'data'}.\n"
            "Django connects by host and port, so it would use that server instead.\n"
            "Stop it, or point PGSQL_HOME and DATABASE_URL at the same cluster."
        )
        return True
    return False


def db_start():
    state = cluster_state()
    if state == CLUSTER_RUNNING:
        print("PostgreSQL is already running.")
        return 0
    if _report_unusable_cluster(state):
        return 1
    if _warn_if_port_is_taken_by_another_server():
        return 1

    code = _pg_ctl("-l", str(PGSQL_HOME / "server.log"), "start", detached=True)
    if code:
        return code

    for _ in range(DB_READY_TIMEOUT):
        time.sleep(1)
        if cluster_state() == CLUSTER_RUNNING and db_is_ready():
            print("PostgreSQL is accepting connections.")
            return 0

    print(f"PostgreSQL did not come up within {DB_READY_TIMEOUT}s.")
    print(f"Check the log: {PGSQL_HOME / 'server.log'}")
    return 1


def db_stop():
    state = cluster_state()
    if _report_unusable_cluster(state):
        return 1
    if state != CLUSTER_RUNNING:
        print("PostgreSQL is not running.")
        return 0
    return _pg_ctl("-m", "fast", "stop")


def db_status():
    state = cluster_state()
    if _report_unusable_cluster(state):
        return 1

    if state == CLUSTER_RUNNING:
        ready = db_is_ready()
        print(f"Cluster at {PGSQL_HOME / 'data'} is running.")
        print(
            "Accepting connections."
            if ready
            else "Running but NOT yet accepting connections."
        )
        return 0 if ready else 1

    print(f"Cluster at {PGSQL_HOME / 'data'} is NOT running.")
    _warn_if_port_is_taken_by_another_server()
    return 1


# --- Validation -----------------------------------------------------------

def check_adr_guards():
    """Enforce the decisions whose ADRs name requirements.txt as the check.

    ADR 0003 defers Django REST Framework; ADR 0005 caps the test stack at five
    packages. Both name requirements.txt as where compliance is visible, so both
    become real checks here rather than aspirational Confirmation prose.
    """
    manifest = BASE_DIR / "requirements.txt"
    print("\n$ adr-guards requirements.txt", flush=True)
    if not manifest.exists():
        print("requirements.txt is missing -- ADR 0003 and 0005 cannot be checked.")
        return 1

    lines = [
        line.split("#")[0].strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
    ]
    packages = [line for line in lines if line]

    failures = []

    drf = [p for p in packages if p.lower().startswith("djangorestframework")]
    if drf:
        failures.append(
            f"ADR 0003 defers Django REST Framework, but requirements.txt has: {', '.join(drf)}.\n"
            "  Either drop it or supersede docs/adr/0003-backend.md."
        )

    test_stack = [
        p for p in packages
        if p.lower().startswith(("pytest", "factory_boy", "factory-boy"))
    ]
    if len(test_stack) > 5:
        failures.append(
            f"ADR 0005 budgets 3-5 test packages; requirements.txt has {len(test_stack)}: "
            f"{', '.join(test_stack)}.\n"
            "  Adding a sixth means revisiting docs/adr/0005-testing.md."
        )

    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print(f"ok: no DRF, {len(test_stack)} test packages (ADR 0005 budget is 3-5)")
    return 0


def validate(extra):
    """The repository's verification entry point (AGENTS.md 13, CLAUDE.md 9).

    Every stage here runs a real command. Do not add a stage for tooling this
    repository does not have -- a stage that prints success without checking
    anything is worse than no stage at all.
    """
    stages = [
        ("Django system checks", lambda: run("manage.py", "check")),
        ("Migration drift", lambda: makemigrations(check=True)),
        ("ADR guards", check_adr_guards),
        # Coverage is reported, not gated -- ADR 0005 chose pytest-cov but sets
        # no threshold. Add --cov-fail-under here once a target is agreed.
        ("Tests", lambda: pytest_suite("test", [*COV_ARGS, *extra])),
    ]

    ran = []
    for name, stage in stages:
        print(f"\n==> {name}")
        code = stage()
        if code:
            print(f"\nFAILED at: {name}")
            print("Stages run: " + ", ".join(ran + [f"{name} (FAILED)"]))
            return code
        ran.append(name)

    print("\nValidation passed. Stages run: " + ", ".join(ran))
    return 0


def pytest_suite(task, extra):
    code = run("-m", "pytest", SUITES[task], *extra)
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

    for task in tasks:
        if task == "migrations":
            code = makemigrations()
        elif task == "migrations:check":
            code = makemigrations(check=True)
        elif task == "db:start":
            code = db_start()
        elif task == "db:stop":
            code = db_stop()
        elif task == "db:status":
            code = db_status()
        elif task == "validate":
            code = validate(extra)
        elif task == "run":
            # Generating migrations is a convenience for the dev server only.
            # Test tasks must never write to the repository.
            code = makemigrations()
            if code == 0:
                code = run("manage.py", "migrate")
            if code == 0:
                code = run("manage.py", "runserver", *extra)
        elif task in SUITES:
            code = makemigrations(check=True)
            if code == 0:
                code = pytest_suite(task, extra)
        else:
            known = ", ".join([
                "run", "validate", "migrations", "migrations:check",
                "db:start", "db:stop", "db:status", *SUITES,
            ])
            print(f"Unknown task '{task}'. Available: {known}")
            return 2

        if code:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
