<h1 align="center">
  <img src="https://github.com/Evalyo/evalyo/blob/master/logo.png?raw=true" width="120px">
  <br>
  Evalyo: Next-Generation Online Judge
</h1>
<p align="center">
  <a href="https://github.com/Evalyo/evalyo/actions?query=workflow%3Abuild">
    <img alt="Build Status" src="https://img.shields.io/github/actions/workflow/status/Evalyo/evalyo/build.yml?branch=master"/>
  </a>
  <a href="LICENSE.md">
    <img alt="License" src="https://img.shields.io/github/license/Evalyo/evalyo"/>
  </a>
  <!-- <a href="https://dmoj.ca/about/discord/">
    <img src="https://img.shields.io/discord/677340492651954177?color=%237289DA&label=Discord"/>
  </a> -->
  <a href="https://pypi.org/project/Django/">
    <img alt="Django 5.2 LTS" src="https://img.shields.io/badge/Django-5.2%20LTS-092E20?logo=django"/>
  </a>
  <a href="https://asgi.readthedocs.io/">
    <img alt="ASGI" src="https://img.shields.io/badge/ASGI-WebSockets-blue"/>
  </a>
</p>

A **modernized**, **easy-to-setup** online judge and contest platform built on Django 5.2 LTS with real-time features powered by ASGI websockets. Based on the proven DMOJ foundation, Evalyo brings cutting-edge performance and simplified deployment to competitive programming platforms.

**Quick Setup • Real-time Updates • Modern UI • High Performance**

## Features

### Modern Architecture
* **Django 5.2 LTS** - Built on the latest long-term support version
* **ASGI WebSockets** - Real-time bidirectional communication
* **Async-first design** - High-performance concurrent request handling
* **Docker-ready** - Containerized deployment with docker-compose
* **Easy setup** - Streamlined installation process with automated configuration

### Performance & Scalability
* [Support for over **60 language runtimes**](https://github.com/DMOJ/online-judge#supported-languages)
* Highly robust judging system:
   * Supports **interactive** and **signature-graded** tasks
   * Supports **runtime data generators** and **custom output validators**
   * Specifying **per-language resource limits**
   * Capable of scaling to hundreds of judging servers
   * **Real-time submission updates** via WebSockets

### Contest Management
* Extremely configurable contest system:
   * Supports ICPC/IOI/AtCoder/ECOO formats out-of-the-box
   * **System testing** supported
   * **Hidden scoreboards** and **virtual participation**
   * [Elo-MMR](https://arxiv.org/abs/2101.00400)-style **rating**
   * **Plagiarism detection** via [Stanford MOSS](https://theory.stanford.edu/~aiken/moss/)
   * Restricting contest access to particular organizations or users

### Content & UI
* Rich problem statements, with support for **LaTeX math and diagrams**
   * Automatic **PDF generation** for easy distribution
   * Built-in support for **editorials**
* **Modern responsive UI** - Mobile-first design with dark mode support
* **Live updates** for submissions with real-time notifications
* Internationalized site interface
* Home page blog and activity stream

### Security & Authentication
* Fine-grained permission control for staff
* OAuth login with Google, Facebook, and Github
* Two-factor authentication support
* **Modern security practices** following Django 5.2 LTS guidelines

## Installation

### Quick Start (Recommended)

Evalyo features a **streamlined setup process** that gets you running in minutes:

```bash
# Clone the repository
git clone https://github.com/Evalyo/evalyo.git
cd evalyo

# Quick setup with Docker (recommended)
docker-compose up -d

# Or use the automated setup script
./scripts/quick-setup.sh
```

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **MySQL 8.0+**
- **Redis 6.0+** (for WebSocket connections and caching)

### Manual Installation

For detailed setup instructions and customization options, check out the install documentation at [docs.dmoj.ca](https://docs.dmoj.ca/#/site/installation).

### Support

<!-- - **Discord**: Join our [Discord community](https://dmoj.ca/about/discord/) for real-time help -->
- **Issues**: Report bugs on [GitHub Issues](https://github.com/Evalyo/evalyo/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/Evalyo/evalyo/discussions)

## Screenshots

### Modern Problem Statements
Rich problem statements written in Markdown with LaTeX-enabled math, interactive diagrams, and modern syntax highlighting. Dark mode support and responsive design ensure optimal reading experience across all devices.

![](https://i.imgur.com/7KD7h5r.png)

### Enhanced Code Submission
Submit in over 60 programming languages with advanced syntax highlighting, auto-completion, and real-time validation. The modern editor supports themes, vim/emacs keybindings, and collaborative features.

![](https://i.imgur.com/8CjfHQb.png)

### ⚡ Real-time Submission Tracking
**ASGI WebSocket-powered** live updates for submission status with instant notifications. Real-time compilation feedback, execution progress, and detailed error reporting with syntax highlighting.

![](https://i.imgur.com/Hom0U3R.png)

Live-updating submission lists with advanced filtering, search capabilities, and real-time status changes. Modern infinite scroll and optimized performance for large datasets.

![](https://i.imgur.com/rc7orzj.png)

### Advanced Contest Management
Feature-rich contest system with real-time leaderboards, virtual participation, and comprehensive analytics. Supports multiple contest formats with customizable scoring and modern WebSocket-based updates.

![](https://i.imgur.com/0V1fzZi.png)

Enhanced contest security with organization restrictions, access codes, and integrated plagiarism detection. Automated editorial publishing and comprehensive contest analytics.

### Responsive Home Interface

Modern, mobile-first home page with real-time activity feeds, upcoming contests, and personalized content recommendations. Clean design with dark mode support.

![](https://i.imgur.com/zpQAoDB.png)

### Internationalization & Accessibility
Comprehensive internationalization support with RTL language compatibility. Visit [translate.dmoj.ca](https://translate.dmoj.ca/) to contribute translations. WCAG 2.1 AA compliant with screen reader support.

![](https://i.imgur.com/OeuI0o5.png)

### Streamlined Administration
Modern Django 5.2 admin interface with enhanced UX, bulk operations, and real-time monitoring. Simplified user management, problem authoring tools, and comprehensive system analytics.

![](https://static.dmoj.ca/data/_other/readme/problem-admin.png)

![](https://static.dmoj.ca/data/_other/readme/admin-dashboard.png)

## Supported languages

Check out [**Evalyo/judge-server**](https://github.com/Evalyo/judge-server) for more judging backend details.

Supported languages include:
* C++ 11/14/17/20 (GCC and Clang)
* C 99/11
* Java 8-22
* Python 2/3
* PyPy 2/3
* Pascal
* Mono C#/F#/VB

The judge can also grade in the languages listed below:
* Ada
* Algol 68
* AWK
* COBOL
* D
* Dart
* Fortran
* Forth
* Go
* Groovy
* GAS x86/x64/ARM
* Haskell
* INTERCAL
* Kotlin
* Lua
* LLVM IR
* NASM x86/x64
* Objective-C
* OCaml
* Perl
* PHP
* Pike
* Prolog
* Racket
* Ruby
* Rust
* Scala
* Chicken Scheme
* sed
* Steel Bank Common Lisp
* Swift
* Tcl
* Turing
* V8 JavaScript
* Brain\*\*\*\*
* Zig

## Development

### Code Quality & Linting

This project uses **Ruff** for fast Python linting and code formatting. Ruff replaces multiple tools (flake8, isort, black, etc.) with a single fast linter written in Rust.

#### Setup

Install development dependencies:
```bash
uv sync --dev
```

#### Running Lints

Use the provided lint script for easy development:

```bash
# Check code style and quality
./scripts/lint.sh

# Apply automatic fixes and format code
./scripts/lint.sh fix
```

Or run Ruff commands directly:

```bash
# Lint checking
uv run ruff check --config pyproject.toml .

# Code formatting
uv run ruff format --config pyproject.toml .

# Apply automatic fixes
uv run ruff check --config pyproject.toml . --fix
```

#### Configuration

Ruff configuration is located in `pyproject.toml` under the `[tool.ruff]` section. The configuration is based on the existing `.flake8` settings with additional modern Python best practices.

Key features enabled:
- Line length: 120 characters (matching legacy flake8 config)
- Import sorting (replaces isort)
- Code formatting (replaces black)
- Django-specific linting rules
- Python 3.12+ modern syntax upgrades
- Comprehensive error checking and style enforcement

#### CI Integration

The GitHub Actions workflow automatically runs Ruff on all pull requests and pushes, ensuring code quality standards are maintained.
