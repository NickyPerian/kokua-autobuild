@echo off
rem simple wrapper for executing build on windows.

set dirname=%~p0
python "%dirname%llbuild" %*
