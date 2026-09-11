"""Project task runner.

    python scripts/dev.py run                 # dev server at 127.0.0.1:8000
    python scripts/dev.py test                # whole suite
    python scripts/dev.py test:unit           # tests/unit only
    python scripts/dev.py test:integration    # tests/integration only
    python scripts/dev.py test:e2e            # tests/e2e only
    python scripts/dev.py migrations          # makemigrations only
    python scripts/dev.py migrations:check    # fail if migrations are missing
    python scripts/dev.py run -- 8080         # pass extra args through
    python scripts/dev.py test:unit -- -x -v

'run' and every 'test' task generate missing migrations first.
'run' also applies them to db.sqlite3 before starting the server.
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
    "test:integration": "tests/integration",
    "test:e2e": "tests/e2e",
}

# Tasks that need the migration state on disk to match the models first.
NEEDS_MIGRATIONS = {"run", *SUITES}


def run(*args):
    """Run a command from the project root, echoing it first."""
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


def main(argv):
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    tasks = argv[:argv.index("--")] if "--" in argv else argv

    if not tasks:
        print(__doc__)
        return 2

    migrated = False
    for task in tasks:
        if task in NEEDS_MIGRATIONS and not migrated:
            code = makemigrations()
            if code:
                return code
            migrated = True

        if task == "migrations":
            code = makemigrations()
        elif task == "migrations:check":
            code = makemigrations(check=True)
        elif task == "run":
            code = run("manage.py", "migrate")
            if code == 0:
                code = run("manage.py", "runserver", *extra)
        elif task in SUITES:
            code = run("-m", "pytest", SUITES[task], *extra)
            if code == NO_TESTS_COLLECTED:
                print(f"({task}: no tests yet - not treated as a failure)")
                code = 0
        else:
            known = ", ".join(["run", "migrations", "migrations:check", *SUITES])
            print(f"Unknown task '{task}'. Available: {known}")
            return 2

        if code:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
