# Data Playbook
:book: Playbooks for data. Open, process and save table based data.

Automate repetitive tasks on table based data. Include various input and output tasks. Can be extended with custom modules.

Install: `pip install dataplaybook`

Use: `dataplaybook playbook.yaml`

## Playbook structure

The playbook.yaml file allows you to load additional modules (containing tasks) and specify the tasks to execute in sequence, with all their parameters.

The `tasks` to perform typically follow the the structure of read, process, write.

Example yaml: (please note yaml is case sensitive)
```yaml
modules: [list, of, modules]

tasks:
  - task: *name
    tables: # List of tables used by this task
    target: # Target table name of this function
    debug*: True/False # default: False
    # task specific properties, refer to each task
```


## Tasks
Tasks are implemented as simple Python functions and the modules can be found in the dataplaybook/tasks folder.

### Default tasks
* drop
* extend
* filter
* fuzzy_match
* print_table
* vlookup

### Module `io_xlsx` (loaded by default)
* read_excel
* write_excel

### Module `io_misc` (loaded by default)
* read_tab_delim
* read_text_regex
* wget
* write_csv

### Module `io_xml`

### Module `ietf`

### Module `gis`

### Module `fnb`
