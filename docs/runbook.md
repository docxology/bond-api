# Run and verify BOND-API

Use Python 3.11 or later and uv. From this repository, install the locked environment and run the SABLE reference provider:

```sh
uv sync --locked --extra dev
uv run python scripts/00_preflight.py
uv run python scripts/demo_mission.py sable
```

The demo discovers the provider in `films/sable/` and prints the result of the five-stage protocol to stdout. The [architecture guide](architecture.md) explains the interfaces and discovery behavior.

## Verify the package

```sh
uv run --extra dev pytest tests/ --cov=src --cov-fail-under=90
uv run --extra dev mypy src/ scripts/ films/
uv run python scripts/z_generate_manuscript_variables.py
```

The hydrator reads [the canonical manuscript config](manuscript/config.yaml) and the live protocol surface. It writes `output/data/manuscript_variables.json` and hydrated Markdown to `output/manuscript/`. Any unresolved token fails the command. Use [the configuration example](manuscript/config.yaml.example) as a starting point for a fork. The hydrator accepts `--config`, `--manuscript-dir`, and `--output-dir` overrides for alternate inputs or an isolated output directory.

Use the pinned template's Ruff settings for lint and formatting. Set `BOND_RUNNER`
to the absolute path of the template checkout prepared below, then run from
the BOND-API checkout:

```sh
uv run --extra dev ruff check --config "$BOND_RUNNER/pyproject.toml" src/ scripts/ films/ tests/
uv run --extra dev ruff format --config "$BOND_RUNNER/pyproject.toml" --check src/ scripts/ films/ tests/
```

## Render and validate the manuscript

Install Python 3.14+, Pandoc 3.14, matching pandoc-crossref v0.3.26b, and XeLaTeX with the [template's TeX packages](https://github.com/docxology/template/blob/87704feae0a4490ef7dad9c931d268e8c30273c2/README.md#L565-L574). Set `BOND_CHECKOUT` to the absolute path of a clean checkout of this repository. From a directory where you can create a fresh runner checkout:

```sh
git clone https://github.com/docxology/template.git bond-template-runner
cd bond-template-runner
git checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
uv sync --locked
project=projects/working/bond-api
mkdir -p projects/working
git -C "$BOND_CHECKOUT" worktree add --detach "$PWD/$project" HEAD
uv run python "$project/scripts/z_generate_manuscript_variables.py"
uv run python scripts/pipeline/stage_03_render.py --project working/bond-api
uv run python scripts/pipeline/stage_04_validate.py --project working/bond-api
```

The runner discovers `docs/manuscript/` and combines its ordered sections, preamble, and bibliography with the hydrated text. Open `$project/output/pdf/bond-api_combined.pdf` and `$project/output/web/index.html` to check section order and citations. The slide PDFs are in `$project/output/slides/`. Validation and source provenance reports are in `$project/output/reports/`.

From the package checkout, check local links with Lychee:

```sh
git diff --check
lychee --offline README.md AGENTS.md 'docs/**/*.md'
```
