"""JMESpath tasks."""
import jmespath as jmespath_lib
import voluptuous as vol

import dataplaybook.config_validation as cv


def valid_jmespath(jmp):
    """Validate JMESpath expressions."""
    try:
        jmespath_lib.compile(jmp)
        return jmp
    except jmespath_lib.exceptions.ParseError as exc:
        raise vol.Invalid("Invalid jmespath expression {}".format(exc))


@cv.task_schema({
    vol.Required('jmespath'): vol.All(str, valid_jmespath),
}, target=1, tables=(0, 1), kwargs=True)
def task_jmespath(table, jmespath):
    """Execute a jmespath expression on a table."""
    print(jmespath)
    return jmespath_lib.search(jmespath, table)
