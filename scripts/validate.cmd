@echo off
REM The repository's verification entry point -- AGENTS.md 13, CLAUDE.md 9.
REM Thin delegate: the stages live in scripts\dev.py so there is one
REM implementation rather than a batch copy that drifts from it.
python "%~dp0dev.py" validate %*
