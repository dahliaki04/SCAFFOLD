# CLAUDE.md — SCAFFOLD

## Project Overview

**SCAFFOLD** is an open-source project scaffold/template repository licensed under AGPL-3.0. It provides a starting point for new projects with foundational conventions, structure, and tooling guidance already in place.

- **Repository**: `dahliaki04/SCAFFOLD`
- **License**: GNU Affero General Public License v3.0 (AGPL-3.0)
- **Status**: Early-stage / greenfield

## Repository Structure

```
SCAFFOLD/
├── .git/            # Git version control
├── LICENSE          # AGPL-3.0 license
├── README.md        # Project readme
└── CLAUDE.md        # This file — AI assistant guide
```

## Development Conventions

### Branching Strategy

- **Default branch**: `main` (or as configured)
- **Feature branches**: Use descriptive names prefixed by category (e.g., `feature/`, `fix/`, `docs/`)
- AI-assisted branches follow the pattern: `claude/<description>-<session-id>`

### Commit Messages

- Use clear, imperative-mood commit messages (e.g., "Add user authentication module")
- Keep the subject line under 72 characters
- Add a body for non-trivial changes explaining the *why*, not just the *what*

### Code Style

- Follow language-specific community conventions as the project grows
- Prefer readability over cleverness
- Keep functions/methods focused and small
- Avoid premature abstraction — duplicate is better than the wrong abstraction

### File Organization

- Group related files by feature or domain, not by file type
- Keep the root directory clean — configuration files only
- Place source code in a `src/` directory (or language-appropriate equivalent)
- Place tests alongside source or in a parallel `tests/` directory

## Building and Running

> **Note**: No build system is configured yet. As the project evolves, update this section with:
> - Build commands (e.g., `make build`, `npm run build`, `cargo build`)
> - Run commands
> - Environment setup instructions
> - Required dependencies and how to install them

## Testing

> **Note**: No test framework is configured yet. When tests are added, document:
> - How to run the full test suite
> - How to run a single test
> - Test naming conventions
> - Coverage requirements

## Linting and Formatting

> **Note**: No linters or formatters are configured yet. When added, document:
> - Lint command (e.g., `npm run lint`, `make lint`)
> - Format command
> - Pre-commit hooks if any

## CI/CD

> **Note**: No CI/CD pipeline is configured yet. When added, document:
> - Pipeline triggers
> - Required checks before merge
> - Deployment process

## AI Assistant Guidelines

When working on this repository:

1. **Read before writing** — Always read existing files before proposing modifications
2. **Minimal changes** — Only change what is requested; avoid unnecessary refactoring
3. **No over-engineering** — Keep solutions simple and focused on the current requirement
4. **Respect the license** — All contributions fall under AGPL-3.0
5. **Update this file** — When adding new tooling, frameworks, or conventions, update the relevant sections of this CLAUDE.md
6. **Security first** — Never commit secrets, credentials, or sensitive data; avoid introducing OWASP Top 10 vulnerabilities
7. **Test your changes** — Run any available tests/linters before committing
