# Contributing to AcouZ

Thank you for your interest in contributing! Here's how to get involved.

---

## Getting Started

1. **Fork** the repository and clone your fork locally.
2. Create a **feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. Set up the development environment (see [README](README.md#installation)).
4. Make your changes, then open a **Pull Request** against `main`.

---

## Branch Naming Conventions

| Prefix | Use case |
|---|---|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `refactor/` | Code restructuring, no behavior change |
| `chore/` | Tooling, CI, dependencies |

---

## Commit Message Format

AcouZ follows the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

**Examples:**

```
feat(hotkey): add configurable hotkey via config.toml
fix(audio): prevent crash when no microphone is detected
docs(readme): add Oracle Cloud self-hosted STT section
```

---

## Code Style

- **Language:** Python 3.11+
- **Formatting:** [Black](https://github.com/psf/black) (line length 100)
- **Type hints:** Required on all public functions and methods
- **Docstrings:** [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- **Comments:** English only

Run Black before committing:
```bash
pip install black
black src/
```

---

## Reporting Bugs

Use the **Bug Report** issue template. Please include:

- Windows version and Python version
- Full terminal output (with `[Error]` lines)
- Steps to reproduce
- Expected vs. actual behavior

---

## Feature Requests

Use the **Feature Request** issue template. Describe the use case, not just the implementation.

---

## Questions

Open a **Discussion** rather than an issue for general questions.
