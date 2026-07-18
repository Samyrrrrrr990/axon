# Security policy

## Supported versions

The latest release on `main` receives security fixes.

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private vulnerability reporting on this repository (Security tab, "Report a vulnerability"), or contact the maintainer through the email on their GitHub profile.

You can expect an acknowledgment within a few days. Please include steps to reproduce and the commit or version you tested.

## Scope notes

- Axon runs untrusted Python in two places by design: the Python code node and agent tool definitions. Both execute with the permissions of the local Axon process. Treat workflow files from strangers the way you treat scripts from strangers: read them before running.
- API keys are stored in plain JSON in the local workspace (`~/.axon/settings.json`) and are sent only to the provider you configure.
- The server binds to `127.0.0.1` and is not designed to be exposed to a network as-is.
