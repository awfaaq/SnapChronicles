# Reliability

When you face a technical choice, choose the most reliable option, the one you are sure will not cause issues.
Run and fix your code until it works.
Commit your changes when it works.
Before a change of the codebase that can break things, you should commit changes so you can revert in case your approach doesn't work.
Reliability includes reproducibility: always open the env before any command.
Reliability includes observability: any long-running or critical path should produce clear logs so progress and failures are visible (avoid silent runs that look frozen).
Prefer timestamped logs with levels (INFO/WARN/ERROR). Log milestones/progress and a final summary (success/failure + key metrics).
When appropriate, write logs to stdout and a file. Avoid noisy default logging in libraries, but allow it to be enabled.

# Files

## ARCHITECTURE.md, the file that describes the project's architecture.

Allows having a global understanding of the project architecture and avoid constantly having to search for files.

Edit it when you :

* add a new code file
* move it
* modify the role of a file
* when you deeply modify the architecture.

The file should be organized in the form of:

* headers and subheaders for the folder tree structure
* Under each directory header containing files, explain the folder role, list the files as bullets and briefly explain how they relatee



\## Makefile



Contains all important commands of the project.

All commands should be annotated with a comment describing the role of the command.



When you create a new script, or change the API of a script, edit the Makefile.



When you delete a script, remove it from the Makefile.

