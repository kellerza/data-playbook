# Data Playbook
[![Build Status](https://travis-ci.com/kellerza/data-playbook.svg?branch=master)](https://travis-ci.com/kellerza/data-playbook)
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
* build_lookup
* combine
* drop
* extend
* filter
* fuzzy_match (`pip install fuzzywuzzy`)
* print
* replace
* unique
* vlookup

### Module `io_xlsx` (loaded by default)
* read_excel
* write_excel

### Module `io_misc` (loaded by default)
* read_csv
* read_tab_delim
* read_text_regex
* wget
* write_csv

### Module `io_mongo` (uses pymongo)
* read_mongo
* write_mongo
* columns_to_list
* list_to_columns

### Module `io_pdf` (requires pdftotext)
* read_pdf_pages
* read_pdf_files

### Module `io_xml`

### Module `ietf`

### Module `gis`

### Module `fnb`


## Yaml Tags

* `!re <expression>` Regular expression
* `!es <search string>` Search a file using Everything


## Install development version

1. Clone the repo
2. `pip install <path> -e`
