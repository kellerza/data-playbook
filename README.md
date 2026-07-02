# Data Playbook

:book: Playbooks for data. Open, process and save table based data.
[![Workflow Status](https://github.com/kellerza/data-playbook/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/kellerza/data-playbook/actions)
[![codecov](https://codecov.io/gh/kellerza/data-playbook/branch/master/graph/badge.svg)](https://codecov.io/gh/kellerza/data-playbook)

Automate repetitive load → process → save workflows on table-based data (`RowData` =
`dict[str, Any]` rows). Built-in tasks cover common input/output formats; custom logic is plain
Python decorated with `@task` and `@playbook`.

Install: `pip install dataplaybook`

```python
from dataplaybook import DataEnvironment, playbook, task
from dataplaybook.tasks.io_misc import read_csv, write_csv


@playbook(default=True)
def my_play(env: DataEnvironment) -> None:
    env["rows"] = list(read_csv(file="data.csv"))
    write_csv(table=env["rows"], file="out.csv")


@task
def uppercase(*, table: list[dict]) -> None:
    for row in table:
        for key, val in row.items():
            if isinstance(val, str):
                row[key] = val.upper()
```

Run: `dataplaybook script.py [playbook_name] [-v] [--all]`

## Core API

```python
from dataplaybook import DataEnvironment, ENV, RowData, Tables, playbook, task
```

| Symbol            | Role                                                |
| ----------------- | --------------------------------------------------- |
| `RowData`         | `dict[str, Any]` — one table row                    |
| `Tables`          | `dict[str, list[RowData]]` or `DataEnvironment`     |
| `DataEnvironment` | Playbook state: named tables plus `var` for scalars |
| `@task`           | Register a keyword-only function as a reusable task |
| `@playbook`       | Entry point; receives `DataEnvironment`             |
| `ENV`             | Module-level `DataEnvironment` singleton            |

Task functions must use keyword-only parameters (`*, table: ...`). They return `list[RowData]`,
`Generator[RowData]`, scalars, or `None`. Generators are consumed into lists when assigned to a
table; non-tabular return values go to `env.var`.

List all registered tasks with signatures:

```bash
dataplaybook --all -vvv
```

## Registered tasks

Grouped by module. Run `dataplaybook --all -vvv` for full signatures.

### `dataplaybook.tasks` — table operations

| Task                | Purpose                                         |
| ------------------- | ----------------------------------------------- |
| `build_lookup`      | Yield lookup rows from a table by key + columns |
| `build_lookup_dict` | Build dict lookup (single or composite key)     |
| `combine`           | Pivot/join multiple tables on a key             |
| `ensure_lists`      | Coerce columns to lists across tables           |
| `filter_rows`       | Include/exclude rows by column values or regex  |
| `print_table`       | Print one table or all tables in env            |
| `remove_null`       | Strip null/empty values from tables             |
| `replace`           | String replace in specified columns             |
| `unique`            | Deduplicate rows by key                         |
| `vlookup`           | Join columns from lookup table into target      |

### `dataplaybook.tasks.fuzzy`

| Task          | Purpose                                                |
| ------------- | ------------------------------------------------------ |
| `fuzzy_match` | Fuzzy-match two tables on columns (needs `fuzzywuzzy`) |

### `dataplaybook.tasks.gis`

| Task         | Purpose                                        |
| ------------ | ---------------------------------------------- |
| `linestring` | Build GIS linestring column from lat/lon pairs |

### `dataplaybook.tasks.ietf`

| Task                           | Purpose                                  |
| ------------------------------ | ---------------------------------------- |
| `extract_standards_from_table` | Extract RFC/IETF refs from text columns  |
| `add_standards_column`         | Add standards column from extracted refs |

Non-task helpers: `extract_standards`, `extract_standards_ordered`, `extract_one_standard`,
`KeyStr`.

### `dataplaybook.tasks.io_mail`

| Task   | Purpose                              |
| ------ | ------------------------------------ |
| `mail` | Send email with optional attachments |

### `dataplaybook.tasks.io_misc`

| Task              | Purpose                                   |
| ----------------- | ----------------------------------------- |
| `file_rotate`     | Rotate numbered backup files              |
| `glob`            | Yield rows from glob patterns             |
| `read_csv`        | Read CSV to rows                          |
| `read_json`       | Read JSON file to rows                    |
| `read_tab_delim`  | Read tab-delimited file with headers      |
| `read_text_regex` | Parse text file with regex newline/fields |
| `wget`            | Download URL to file (skip if fresh)      |
| `write_csv`       | Write table to CSV                        |
| `write_json`      | Write tables or rows to JSON              |

### `dataplaybook.tasks.io_mongo`

Requires `pip install dataplaybook[mongo]`.

| Task                | Purpose                                    |
| ------------------- | ------------------------------------------ |
| `read_mongo`        | Read MongoDB set to rows                   |
| `write_mongo`       | Write rows to MongoDB set                  |
| `columns_to_list`   | Flatten columns into a list column         |
| `list_to_columns`   | Expand list column into separate columns   |
| `mongo_list_sids`   | List set IDs in a MongoDB database         |
| `mongo_delete_sids` | Delete sets by ID                          |
| `mongo_sync_sids`   | Sync sets between local and remote MongoDB |

Async helpers (not `@task`): `read_mongo_async`, `write_mongo_async`, `mongo_list_sids_async`,
`delete_sids_async`, `mongo_sync_sids_async`, `get_remote_client`.

### `dataplaybook.tasks.io_pdf`

Requires `pdftotext` on PATH.

| Task             | Purpose                       |
| ---------------- | ----------------------------- |
| `read_pdf_pages` | Read PDF pages as rows        |
| `read_pdf_files` | Read PDFs from folder as rows |

### `dataplaybook.tasks.io_xlsx`

| Task          | Purpose                                            |
| ------------- | -------------------------------------------------- |
| `read_excel`  | Read Excel sheets into named tables                |
| `write_excel` | Write tables to Excel (supports `Sheet`, `Column`) |

### `dataplaybook.tasks.io_xml`

| Task        | Purpose                                  |
| ----------- | ---------------------------------------- |
| `read_xml`  | Parse XML targets into tables (stdlib)   |
| `read_lxml` | Parse XML with lxml (needs `lxml` extra) |

Define domain tasks in your own script with `@task`. Import `dataplaybook.tasks.all` or specific
task modules to preload built-ins.

## Utilities

### `dataplaybook.utils` — general

| Symbol                          | Purpose                                   |
| ------------------------------- | ----------------------------------------- |
| `slugify(text)`                 | Lowercase slug for var/table keys         |
| `time_it(name, delta, logger)`  | Context manager; warn on slow runs        |
| `local_import_module(mod_name)` | Import `.py` from cwd (used by CLI)       |
| `doublewrap`                    | Decorator helper for optional args        |
| `PlaybookError`                 | Recoverable playbook exception            |
| `AttrDict`                      | Read-only recursive dict attribute access |

Re-exported from submodules:

| Symbol                                                                                                                                                           | Module         | Purpose               |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | --------------------- |
| `ensure_bool`, `ensure_bool_str`, `ensure_naive_datetime`, `ensure_instant`, `ensure_dict`, `ensure_list`, `ensure_list_from_str`, `ensure_set`, `ensure_string` | `utils.ensure` | Coerce untyped values |
| `append_unique`, `extract_pattern`, `strip`, `unique`                                                                                                            | `utils.lists`  | List helpers          |

### `dataplaybook.utils.json`

| Symbol                         | Purpose                      |
| ------------------------------ | ---------------------------- |
| `orjson_dumpb`, `orjson_dumps` | Fast JSON serialize (orjson) |
| `orjson_load`, `orjson_aload`  | Load JSON sync/async         |
| `write_orjson`                 | Write JSON file              |

### `dataplaybook.utils.cache`

| Symbol                  | Purpose                                           |
| ----------------------- | ------------------------------------------------- |
| `CacheDict`             | TTL cache (minutes) with `clear`, `get`, `get_as` |
| `CACHE`                 | Global `CacheDict` (30 min default)               |
| `cache_return(minutes)` | Async decorator to cache function results         |

### `dataplaybook.utils.prettytable`

| Symbol         | Purpose                                               |
| -------------- | ----------------------------------------------------- |
| `pretty_table` | Build `PrettyTable` from headers + rows               |
| `table_data`   | Convert `list[dict]` to headers + row matrix          |
| `StatSummary`  | Accumulate labelled stat rows and print summary table |

### `dataplaybook.utils.logger`

| Symbol                                           | Purpose                          |
| ------------------------------------------------ | -------------------------------- |
| `get_logger`, `set_logger_level`, `setup_logger` | Colorlog setup and level control |

### `dataplaybook.utils.parser` — structuring untrusted dicts

| Symbol                     | Purpose                                                                                      |
| -------------------------- | -------------------------------------------------------------------------------------------- |
| `BaseClass`                | Dataclass base: `structure`, `structure_list`, `structure_iter`, `async_structure`, `asdict` |
| `Parser`, `create_step`    | Field-rename/coerce recipe for row dicts                                                     |
| `pre_process`              | Class decorator: unknown fields, parser hooks                                                |
| `CONVERT`, `get_converter` | Shared `cattrs.Converter` with type hooks                                                    |
| `structure1`               | One-shot structure via converter                                                             |

### `dataplaybook.helpers`

| Symbol                        | Module          | Purpose                                          |
| ----------------------------- | --------------- | ------------------------------------------------ |
| `DataEnvironment`, `DataVars` | `helpers.env`   | Playbook state (also exported from package root) |
| `parse_args`                  | `helpers.args`  | CLI arg parsing (`DPArg`)                        |
| `repr_signature`, `repr_call` | `helpers.typeh` | Task signature logging                           |

### `dataplaybook.everything`

| Symbol           | Purpose                                               |
| ---------------- | ----------------------------------------------------- |
| `search(*terms)` | Find files via Everything HTTP API (`localhost:8881`) |
| `Result`         | `total`, `files`, `folders`                           |

### `dataplaybook.main`

| Symbol                            | Purpose                           |
| --------------------------------- | --------------------------------- |
| `ALL_TASKS`                       | Registry of all `@task` functions |
| `print_tasks()`                   | Print registered tasks to stderr  |
| `run_playbooks(dataplaybook_cmd)` | Execute playbook from CLI args    |
| `get_default_playbook(module)`    | Resolve default `@playbook` name  |

### Optional extras

| Extra / dep                         | Enables                             |
| ----------------------------------- | ----------------------------------- |
| `dataplaybook[mongo]`               | MongoDB tasks + async motor helpers |
| `dataplaybook[all]`                 | lxml, mongo, python-pptx            |
| `fuzzywuzzy` + `python-levenshtein` | `fuzzy_match`                       |
| `pdftotext` binary                  | PDF tasks                           |
| Everything (voidtools)              | `everything.search` file resolution |

## Local development

uv is used for dependency management. To install the dependencies.

```bash
uv sync --all-extras
```

pre-commit is used for code formatting and linting. Install pre-commit and run `pre-commit install`
to install the git hooks.

```bash
uv tool install prek
prek install
```

Test locally using pre-commit (ruff, codespell, mypy)

```bash
git add . && prek
```

## Data Playbook v0 - origins

Data playbooks was created to replace various snippets of code I had lying around. They were all
created to ensure repeatability of some menial task, and generally followed a similar structure of
load something, process it and save it. (Process network data into GIS tools, network audits &
reporting on router & NMS output, Extract IETF standards to complete SOCs, read my bank statements
into my Excel budgeting tool, etc.)

For many of these tasks I have specific processing code (`tasks_x.py`, loaded with
`modules: [tasks_x]` in the playbook), but in almost all cases input & output tasks (and configuring
these names etc) are common. The idea of the modular tasks originally came from Home Assistant,
where I started learning Python and the idea of "custom components" to add your own integrations,
although one could argue this also has similarities to Ansible playbooks.

In many cases I have a 'loose' coupling to actual file names, using Everything search
(`!es search_pattern` in the playbook) to resolve a search pattern to the correct file used for
input.

It has some parts in common with Ansible Playbooks, especially the name was chosen after I was
introduced to Ansible Playbooks. The task structure has been updated in 2019 to match the Ansible
Playbooks 2.0/2.5+ format and allow names. This format will also be easier to introduce loop
mechanisms etc.

### Comparison to Ansible Playbooks

Data playbooks is intended to create and modify variables in the environment (similar to
**inventory**). Data playbooks starts with an empty environment (although you can read the
environment from various sources inside the play). Although new variables can be created using
**register:** in Ansible, data playbook functions requires the output to be captured through
`target:`.

Data playbook tasks are different form Ansible's **actions**:

- They are mostly not idempotent, since the intention is to modify tables as we go along,
- they can return lists containing rows or be Python iterators (that `yield` rows of a table)
- if they dont return any tabular data (a list), the return value will be added to the `var` table
  in the environment
- Each task is type-checked at runtime via `typeguard` to allow quick troubleshooting

You could argue I can do this with Ansible, but it won't be as elegant with single item hosts files,
`gather_facts: no` and `delegate_to: localhost` throughout the playbooks. It will likely only be
half as much fun trying to force it into my way of thinking.

## Release

Semantic versioning is used for release.

To create a new release, include a commit with a :dolphin: emoji as a prefix in the commit message.
This will trigger a release on the master branch.

```bash
# Patch
git commit -m ":dolphin: Release 0.0.x"

# Minor
git commit -m ":rocket: Release 0.x.0"
```
