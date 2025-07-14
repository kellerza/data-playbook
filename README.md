# Data Playbook

:book: Playbooks for data. Open, process and save table based data.
[![Workflow Status](https://github.com/kellerza/data-playbook/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/kellerza/data-playbook/actions)
[![codecov](https://codecov.io/gh/kellerza/data-playbook/branch/master/graph/badge.svg)](https://codecov.io/gh/kellerza/data-playbook)

Automate repetitive tasks on table based data. Include various input and output tasks.

Install: `pip install dataplaybook`

Use the `@task` and `@playbook` decorators

```python
from dataplaybook import task, playbook
from dataplaybook.tasks.io_xlsx

@task
def print
```

## Tasks

Tasks are implemented as simple Python functions and the modules can be found in the dataplaybook/tasks folder.

| Description                                      | Module                        | Functions                                                                                      |
|:-------------------------------------------------|-------------------------------|:-----------------------------------------------------------------------------------------------|
| Generic function to work on tables               | `dataplaybook.tasks`          | build_lookup, build_lookup_var, combine, drop, extend, filter, print, replace, unique, vlookup |
| Fuzzy string matching                            | `dataplaybook.taksk.fuzzy`    | Requires _pip install fuzzywuzzy_                                                              |
| Read/write excel files ()                        | `dataplaybook.tasks.io_xlsx`  | read_excel, write_excel                                                                        |
| Misc IO tasks                                    | `dataplaybook.tasks.io_misc`  | read_csv, read_tab_delim, read_text_regex, wget, write_csv                                     |
| MongoDB functions                                | `dataplaybook.tasks.io_mongo` | read_mongo, write_mongo, columns_to_list, list_to_columns                                      |
| PDF functions. Requires _pdftotext_ on your path | `dataplaybook.tasks.io_pdf`   | read_pdf_pages, read_pdf_files                                                                 |
| Read XML                                         | `dataplaybook.tasks.io_xml`   | read_xml                                                                                       |

```bash
$ dataplaybook --all -vvv
dataplaybook.tasks
- build_lookup "(*, table: list[RowData], key: str, columns: list[str]) -> RowDataGen"
- build_lookup_dict "(*, table: list[RowData], key: str | list[str], columns: list[str] | None = None) -> dict[str | tuple, Any]"
- combine "(*, tables: list[list[RowData]], key: str, columns: list[str], value: Union[Literal[True], str] = True) -> list[RowData]"
- ensure_lists "(*, tables: Sequence[list[RowData]], columns: Sequence[str]) -> None"
- filter_rows "(*, table: list[RowData], include: dict[str, str] | None = None, exclude: dict[str, str | list[str] | re.Pattern] | None
= None) -> RowDataGen"
- print_table "(*, table: list[RowData] | None = None, tables: dict[str, list[RowData]] | DataEnvironment | None = None) -> None"
- remove_null "(*, tables: Sequence[list[RowData]]) -> None"
- replace "(*, table: list[RowData], replace_dict: dict[str, str], columns: list[str]) -> None"
- unique "(*, table: list[RowData], key: str) -> RowDataGen"
- vlookup "(*, table0: list[RowData], acro: list[RowData], columns: list[str]) -> None"
dataplaybook.tasks.fuzzy
- fuzzy_match "(*, table1: list[RowData], table2: list[RowData], t1_column: str, t2_column: str, t1_target_column: str) -> None"
dataplaybook.tasks.ietf
- add_standards_column "(*, table: list[RowData], columns: list[str], rfc_col: str) -> None"
- extract_standards_from_table "(*, table: list[RowData], extract_columns: list[str], include_columns: list[str] | None = None, name: str = '', line_offset: int = 1) -> RowDataGen"
dataplaybook.tasks.gis
- linestring "(*, table: list[RowData], lat_a: str = 'latA', lat_b: str = 'latB', lon_a: str = 'lonA', lon_b: str = 'lonB', linestring_column: str = 'linestring', error: str = '22 -22') -> list[RowData]"
dataplaybook.tasks.io_mail
- mail "(*, to_addrs: list[str] | str, from_addr: str, subject: str, server: str, files: list[str] | None = None, priority: int = 4, body: str | None = '', html: str | None = '', cc_addrs: list[str] | None = None, bcc_addrs: list[str] | None = None) -> None"
dataplaybook.tasks.io_misc
- file_rotate "(*, file: os.PathLike | str, count: int = 3) -> None"
- glob "(*, patterns: list[str]) -> RowDataGen"
- read_csv "(*, file: os.PathLike | str, columns: dict[str, str] | None = None) -> RowDataGen"
- read_json "(*, file: os.PathLike | str) -> list[RowData]"
- read_tab_delim "(*, file: os.PathLike | str, headers: list[str]) -> RowDataGen"
- read_text_regex "(*, file: os.PathLike | str, newline: re.Pattern, fields: re.Pattern | None) -> RowDataGen"
- wget "(*, url: str, file: os.PathLike | str, age: int = 172800, headers: dict[str, str] | None = None) -> None"
- write_csv "(*, table: list[RowData], file: os.PathLike | str, header: list[str] | None = None) -> None"
- write_json "(*, data: dict[str, list[RowData]] | DataEnvironment | list[RowData], file: os.PathLike | str, only_var: bool = False) ->
None"
dataplaybook.tasks.io_mongo
- columns_to_list "(*, table: 'list[RowData]', list_column: 'str', columns: 'list[str]') -> 'None'"
- list_to_columns "(*, table: 'list[RowData]', list_column: 'str', columns: 'list[str]') -> 'None'"
- mongo_delete_sids "(*, mdb: 'MongoURI', sids: 'list[str]') -> 'None'"
- mongo_list_sids "(*, mdb: 'MongoURI') -> 'list[str]'"
- mongo_sync_sids "(*, mdb_local: 'MongoURI', mdb_remote: 'MongoURI', ignore_remote: 'abc.Sequence[str] | None' = None, only_sync_sids:
'abc.Sequence[str] | None' = None) -> 'None'"
- read_mongo "(*, mdb: 'MongoURI', set_id: 'str | None' = None) -> 'RowDataGen'"
- write_mongo "(*, table: 'list[RowData]', mdb: 'MongoURI', set_id: 'str | None' = None, force: 'bool' = False) -> 'None'"
dataplaybook.tasks.io_pdf
- read_pdf_files "(*, folder: str, pattern: str = '*.pdf', layout: bool = True, args: list[str] | None = None) -> RowDataGen"
- read_pdf_pages "(*, file: os.PathLike | str, layout: bool = True, args: list[str] | None = None) -> RowDataGen"
dataplaybook.tasks.io_xlsx
- read_excel "(*, tables: dict[str, list[RowData]] | DataEnvironment, file: os.PathLike | str, sheets: list[dataplaybook.tasks.io_xlsx.Sheet] | None = None) -> list[str]"
- write_excel "(*, tables: dict[str, list[RowData]] | DataEnvironment, file: os.PathLike | str, include: list[str] | None = None, sheets: list[dataplaybook.tasks.io_xlsx.Sheet] | None = None, ensure_string: bool = False) -> None"
dataplaybook.tasks.io_xml
- read_lxml "(*, tables: dict[str, list[RowData]] | DataEnvironment, file: str, targets: list[str]) -> None"
- read_xml "(*, tables: dict[str, list[RowData]] | DataEnvironment, file: str, targets: list[str]) -> None"
```

## Local development

uv is used for dependency management. To install the dependencies.

```bash
uv sync
```

pre-commit is used for code formatting and linting. Install pre-commit and run `pre-commit install` to install the git hooks.

```bash
pip install pre-commit && pre-commit install
```

Test locally using pre-commit (ruff, codespell, mypy)

```bash
git add . && pre-commit run --all
```

## Data Playbook v0 - origins

Data playbooks was created to replace various snippets of code I had lying around. They were all created to ensure repeatability of some menial task, and generally followed a similar structure of load something, process it and save it. (Process network data into GIS tools, network audits & reporting on router & NMS output, Extract IETF standards to complete SOCs, read my bank statements into my Excel budgeting tool, etc.)

For many of these tasks I have specific processing code (`tasks_x.py`, loaded with `modules: [tasks_x]` in the playbook), but in almost all cases input & output tasks (and configuring these names etc) are common. The idea of the modular tasks originally came from Home Assistant, where I started learning Python and the idea of "custom components" to add your own integrations, although one could argue this also has similarities to Ansible playbooks.

In many cases I have a 'loose' coupling to actual file names, using Everything search (`!es search_pattern` in the playbook) to resolve a search pattern to the correct file used for input.

It has some parts in common with Ansible Playbooks, especially the name was chosen after I was introduced to Ansible Playbooks. The task structure has been updated in 2019 to match the Ansible Playbooks 2.0/2.5+ format and allow names. This format will also be easier to introduce loop mechanisms etc.

### Comparison to Ansible Playbooks

Data playbooks is intended to create and modify variables in the environment (similar to **inventory**). Data playbooks starts with an empty environment (although you can read the environment from various sources inside the play).
Although new variables can be created using **register:** in Ansible, data playbook functions requires the output to be captured through `target:`.

Data playbook tasks are different form Ansible's **actions**:

- They are mostly not idempotent, since the intention is to modify tables as we go along,
- they can return lists containing rows or be Python iterators (that `yield` rows of a table)
- if they dont return any tabular data (a list), the return value will be added to the `var` table in the environment
- Each have a strict voluptuous schema, evaluated when loading and during runtime (e.g. to expand templates) to allow quick troubleshooting

You could argue I can do this with Ansible, but it won't be as elegant with single item hosts files, `gather_facts: no` and `delegate_to: localhost` throughout the playbooks. It will likely only be half as much fun trying to force it into my way of thinking.

## Release

Semantic versioning is used for release.

To create a new release, include a commit with a :dolphin: emoji as a prefix in the commit message. This will trigger a release on the master branch.

```bash
# Patch
git commit -m ":dolphin: Release 0.0.x"

# Minor
git commit -m ":rocket: Release 0.x.0"
```
