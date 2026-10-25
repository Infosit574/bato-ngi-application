# Agent guidance for this repository

These rules are binding for every agent and every human contributor working in this repository. They apply to every change, whether or not the task brief mentions them. A change that violates them is not acceptable and must be revised before review can pass.

## Rule 1. A configuration change requires an ADR

Any change that adds, renames or removes a configuration setting (an environment variable, a Compose variable or a configuration file key) must include a new file docs/adr/ADR-NNNN-<slug>.md with the sections Context, Decision and Consequences. NNNN is the next free number, starting at 0001.

## Rule 2. Conventional Commits

Every commit subject has the form type(scope): description, with type one of feat, fix, docs, chore, refactor or test.

Owner of these rules: Infosit d.o.o.
