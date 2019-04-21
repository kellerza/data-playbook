"""JMESpath tasks."""
import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook.templates import process_template_str, TEMPLATE_JMES


@cv.task_schema({
    vol.Required('jmespath'): cv.isjmespath,
}, target=1, tables=(0, 1), kwargs=True)
def task_jmespath(table, jmespath):
    """Execute a jmespath expression on a table."""
    return process_template_str(f"{TEMPLATE_JMES} {jmespath}", table)


@cv.task_schema({
    cv.slug: cv.templateSchema()
}, target=0, tables=(0, 0))
def task_set(env, opt):
    """Execute a jmespath expression on a table."""
    for key, val in opt.items():
        env.var[key] = val
