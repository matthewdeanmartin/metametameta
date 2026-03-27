# Kilo Roadmap for metametameta

> A vision for the future of automated Python package metadata generation

## Project Overview

metametameta generates `__about__.py` files with dunder metadata (`__version__`, `__author__`, etc.) from various Python packaging sources (PEP 621, Poetry, setup.cfg, setup.py, importlib.metadata).

______________________________________________________________________

## 🚀 Phase 1: Enhanced Source Support

### 1.1 Additional Package Managers

| Priority | Feature | Description |
|----------|---------|-------------|
| High | **PDM Support** | Generate from `pyproject.toml` using `[tool.pdm]` section |
| High | **Hatch Support** | Support `[tool.hatch.metadata]` configuration |
| Medium | **Flit Support** | Parse `pyproject.toml` with `[tool.flit]` section |
| Medium | **Poetry 2.0** | Handle new Poetry `package` configuration format |
| Low | **Meson Python** | Extract metadata from Meson build configurations |

### 1.2 Alternative Metadata Files

| Priority | Feature | Description |
|----------|---------|-------------|
| High | **setup.py parse improvements** | Support more complex setup.py patterns (dynamic versions, conditionals) |
| Medium | **pdm.lock parsing** | Extract version from `pdm.lock` for locked versions |
| Medium | **requirements.txt** | Generate minimal `__about__.py` from requirements files |
| Low | **conda/meta.yaml** | Extract metadata from Conda recipes |

______________________________________________________________________

## 🔧 Phase 2: CLI Enhancements

### 2.1 Interactive Mode

```bash
mmminit          # Interactive wizard to set up metadata generation
mmminit --force  # Re-run setup wizard
```

A guided flow that:

- Detects existing packaging setup
- Asks user preferences (output location, variables to include)
- Generates appropriate configuration file
- Optionally adds to CI/CD

### 2.2 Watch Mode

```bash
mmmw  # Watch mode - auto-regenerate on file changes
mmmw --debounce 1.0  # Debounce by 1 second
```

Uses file system watchers to detect changes to source files and automatically regenerate `__about__.py`.

### 2.3 Template System

```bash
mmm generate --template minimal    # Just version
mmm generate --template standard    # Standard metadata
mmm generate --template full        # All available fields
mmm generate --template custom      # User-defined template
```

Custom templates for different use cases:

- PyPI-ready metadata
- Internal package metadata
- Minimal for performance
- Extended with non-standard fields

### 2.4 Diff & Preview

```bash
mmm diff           # Show what would change without writing
mmm diff --color   # Colored diff output
mmm preview        # Preview generated file without writing
```

Preview changes before writing, useful for CI validation.

______________________________________________________________________

## 🔒 Phase 3: CI/CD Integration

### 3.1 GitHub Actions

```yaml
# .github/workflows/update-about.yml
- uses: matthewdeanmartin/metametameta-action@v1
  with:
    source: pep621
    validate: true
    comment-on-pr: true
```

- **Official GitHub Action** for easy CI integration
- Auto-create PR with `__about__.py` updates
- Fail CI if metadata is out of sync

### 3.2 Pre-commit Hook

```yaml
# .pre-commit-hooks.yaml
- id: update-about
  name: Update __about__.py
  entry: mmm auto --validate
  pass_filenames: false
  always_run: true
```

Auto-update metadata on commit.

### 3.3 Git Hook Integration

```bash
mmm install-hook   # Install git pre-commit hook
mmm uninstall-hook # Remove git hook
```

______________________________________________________________________

## 📊 Phase 4: Metadata Intelligence

### 4.1 Extended Field Support

| Field | Source | Description |
|-------|--------|-------------|
| `__changelog__` | CHANGELOG.md | Link to changelog file |
| `__docker_image__` | pyproject.toml | Container image name |
| `__code_quality__` | SonarQube | Code quality metrics |
| `__ci_status__` | GitHub Actions | Latest CI status badge |
| `__test_coverage__` | Codecov | Coverage percentage |
| `__pypi_downloads__` | PyPI | Download count |
| `__dependents__` | libraries.io | Number of dependents |

### 4.2 Dynamic Metadata

```python
# __about__.py with dynamic values
__commit_hash__ = "{{COMMIT_HASH}}"
__build_date__ = "{{BUILD_DATE}}"
__ci_url__ = "{{CI_BUILD_URL}}"
```

Support placeholder values that get filled during build/CI:

- Git commit SHA
- Build timestamp
- CI/CD URLs
- Version from tags

### 4.3 Metadata Validation

```bash
mmm validate              # Validate __about__.py matches source
mmm validate --strict     # Strict mode: fail on any mismatch
mmm validate --report    # Generate validation report
```

- Validate consistency between `__about__.py` and source
- Check for deprecated fields
- Warn about missing recommended fields

______________________________________________________________________

## 🛠 Phase 5: Developer Experience

### 5.1 IDE Integration

- **VS Code extension** with metadata snippets
- **PyCharm plugin** for visual metadata editing
- **Emacsminor mode** for elisp-less editing

### 5.2 Plugin System

```python
# mmm_plugins.py
def transform_metadata(metadata: dict) -> dict:
    """Add custom transformations."""
    metadata["__custom_field__"] = compute_value()
    return metadata
```

- Custom transformation hooks
- Additional field processors
- Output format plugins (JSON, TOML, YAML)

### 5.3 Configuration File

```toml
# .metametameta.toml
[tool.metametameta]
source = "pep621"
output = "mypackage/__about__.py"
validate = true

[tool.metametameta.fields]
include = ["version", "author", "description"]
exclude = ["classifiers"]

[tool.metametameta.template]
path = "templates/about.py.j2"
```

### 5.4 GraphQL API

```python
import metametameta as mmm

# Programmatic with more options
result = mmm.generate(
    source="pep621",
    output="__about__.py",
    template="custom",
    transform=my_transform,
    dry_run=True
)
```

______________________________________________________________________

## 🌐 Phase 6: Ecosystem Expansion

### 6.1 Multi-Language Support

- **Ruby gemspec** → Python `__about__.py` converter
- **NPM package.json** → Python metadata converter
- **Cargo.toml** → Python metadata converter
- **Go go.mod** → Python metadata converter

### 6.2 Package Index Integration

```bash
mmm sync              # Sync with PyPI
mmm sync --local     # Update from local package
mmm diff pypi        # Compare local vs PyPI metadata
```

- Fetch metadata from PyPI/API
- Compare local vs published metadata
- Bulk update multiple packages

### 6.3 Documentation Generation

```bash
mmm docs             # Generate API reference from __about__.py
mmm badge            # Generate badges (version, license, etc.)
```

Generate:

- Package badges for README
- Metadata summary tables
- API documentation snippets

______________________________________________________________________

## 📈 Phase 7: Analytics & Insights

### 7.1 Package Analysis

```bash
mmm analyze              # Analyze this package
mmm analyze --compare    # Compare two packages
mmm audit                # Audit dependencies
```

- Package health scores
- Metadata completeness analysis
- Dependency chain visualization

### 7.2 Reporting

- Generate `METADATA.md` with package stats
- Export to JSON/CSV for external tools
- Dashboard for monorepo management

______________________________________________________________________

## 🔮 Future Speculations

### AI-Assisted Metadata

- Use LLM to suggest missing fields
- Auto-generate descriptions from code
- Detect author information from git history

### Blockchain Verification

- Anchor metadata hashes on blockchain
- Prove metadata existed at certain time
- Immutable audit trail

### Decentralized Registry

- IPFS-based metadata storage
- ENS domain integration
- Web3 package discovery

______________________________________________________________________

## 📋 Feature Priority Matrix

| Feature | Complexity | Impact | Priority |
|---------|------------|--------|----------|
| PDM/Hatch support | Low | High | P0 |
| Configuration file | Medium | High | P0 |
| Diff/preview mode | Low | High | P0 |
| GitHub Action | Medium | High | P0 |
| Watch mode | Medium | Medium | P1 |
| Template system | Medium | Medium | P1 |
| Interactive wizard | Medium | Medium | P1 |
| Extended fields | Low | Medium | P2 |
| Pre-commit hook | Low | Medium | P2 |
| IDE integration | High | Medium | P2 |
| Multi-language | Medium | Low | P3 |
| Plugin system | High | Medium | P3 |
| AI assistance | High | Low | P3 |

______________________________________________________________________

## 🗺 Release Roadmap

### v0.2 - Configuration & Templates

- `.metametameta.toml` configuration
- Template system
- Diff/preview mode

### v0.3 - CI/CD Integration

- Official GitHub Action
- Pre-commit hook
- Configuration file support

### v0.4 - Watch & Interactive

- Watch mode
- Interactive wizard
- Extended field support

### v0.5 - Ecosystem

- PDM/Hatch support
- Multi-language converters
- Package index integration

### v1.0 - Stable

- Plugin system
- GraphQL API
- Full documentation

______________________________________________________________________

*This roadmap is a living document. Priorities may shift based on community feedback and usage patterns.*
