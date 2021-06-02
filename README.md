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

| Module                                                                                     | Functions                                                                                      |
| :----------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------- |
| Generic function to work on tables<br>`dataplaybook.tasks`                                 | build_lookup, build_lookup_var, combine, drop, extend, filter, print, replace, unique, vlookup |
| Fuzzy string matching <br>`dataplaybook.taksk.fuzzy`<br> Requires _pip install fuzzywuzzy_ |                                                                                                |
| Read/write excel files ()<br>`dataplaybook.tasks.io_xlsx`                                  | read_excel, write_excel                                                                        |
| Misc IO tasks<br>`dataplaybook.tasks.io_misc`                                              | read_csv, read_tab_delim, read_text_regex, wget, write_csv                                     |
| MongoDB functions<br>`dataplaybook.tasks.io_mongo`                                         | read_mongo, write_mongo, columns_to_list, list_to_columns                                      |
| PDF functions. Requires _pdftotext_ on your path<br>`dataplaybook.tasks.io_pdf`            | read_pdf_pages, read_pdf_files                                                                 |
| Read XML<br>`dataplaybook.tasks.io_xml`                                                    | read_xml                                                                                       |

## Data Playbook v0

The [v0](https://github.com/kellerza/data-playbook/tree/v0) of dataplaybook used yaml files, very similar to playbooks

Use: `dataplaybook playbook.yaml`

### Playbook structure

The playbook.yaml file allows you to load additional modules (containing tasks) and specify the tasks to execute in sequence, with all their parameters.

The `tasks` to perform typically follow the the structure of read, process, write.

Example yaml: (please note yaml is case sensitive)

```yaml
modules: [list, of, modules]

tasks:
  - task_name: # See a list of tasks below
      task_setting_1: 1
    tables: # The INPUT. One of more tables used by this task
    target: # The OUTPUT. Target table name of this function
    debug: True/False # Print extra debug message, default: False
```

### Templating

Jinja2 and JMESPath expressions can be used to create parameters for subsequent tasks. Jinja2 simply use the `"{{ var[res1] }}"` bracket syntax and jmespath expressions should start with the word _jmespath_ followed by a space.

Both the `vars` and `template` tasks achieve a similar result: (this will search a table matching string "2" on the key column and return the value in the value column)

```yaml
- vars:
    res1: jmespath test[?key=='2'].value | [0]
# is equal to
- template:
    jmespath: "test[?key=='2'].value | [0]"
  target: res1
# ... then use it with `{{ var.res1 }}`
```

The JMESpath task `template` task has an advantage that you can create new variables **or tables**.

If you have a lookup you use regularly you can do the following:

```yaml
 - build_lookup_var:
     key: key
     columns: [value]
   target: lookup1
  # and then use it as follows to get a similar results to the previous example
  - vars:
      res1: "{{ var['lookup1']['2'].value }}"
```

When searching through a table with Jinja, a similar one-liner, using `selectattr`, seems much more complex:

```yaml
- vars:
    res1: "{{ test | selectattr('key', 'equalto', '2') | map(attribute='value') | first }}"
```

### Special yaml functions

- `!re <expression>` Regular expression
- `!es <search string>` Search a file using Everything by Voidtools

### Install the development version

1. Clone the repo
2. `pip install <path> -e`

### Data Playbook v0 origins

Data playbooks was created to replace various snippets of code I had lying around. They were all created to ensure repeatability of some menial task, and generally followed a similar structure of load something, process it and save it. (Process network data into GIS tools, network audits & reporting on router & NMS output, Extract IETF standards to complete SOCs, read my bank statements into my Excel budgeting tool, etc.)

For many of these tasks I have specific processing code (`tasks_x.py`, loaded with `modules: [tasks_x]` in the playbook), but in almost all cases input & output tasks (and configuring these names etc) are common. The idea of the modular tasks originally came from Home Assistant, where I started learning Python and the idea of "custom components" to add your own integrations, although one could argue this also has similarities to Ansible playbooks.

In many cases I have a 'loose' coupling to actual file names, using Everything search (`!es search_pattern` in the playbook) to resolve a search pattern to the correct file used for input.

It has some parts in common with Ansible Playbooks, especially the name was chosen after I was introduced to Ansible Playbooks. The task structure has been updated in 2019 to match the Ansible Playbooks 2.0/2.5+ format and allow names. This format will also be easier to introduce loop mechanisms etc.

#### Comparison to Ansible Playbooks

Data playbooks is intended to create and modify variables in the environment (similar to **inventory**). Data playbooks starts with an empty environment (although you can read the environment from various sources inside the play).
Although new variables can be created using **register:** in Ansible, data playbook functions requires the output to be captured through `target:`.

Data playbook tasks are different form Ansible's **actions**:

- They are mostly not idempotent, since the intention is to modify tables as we go along,
- they can return lists containing rows or be Python iterators (that `yield` rows of a table)
- if they dont return any tabular data (a list), the return value will be added to the `var` table in the environment
- Each have a strict voluptuous schema, evaluated when loading and during runtime (e.g. to expand templates) to allow quick troubleshooting

You could argue I can do this with Ansible, but it won't be as elegant with single item hosts files, `gather_facts: no` and `delegate_to: localhost` throughout the playbooks. It will likely only be half as much fun trying to force it into my way of thinking.
