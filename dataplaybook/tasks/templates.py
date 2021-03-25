# """JMESpath tasks."""
# import logging

# import voluptuous as vol

# import dataplaybook.config_validation as cv
# from dataplaybook.templates import process_template_str, TEMPLATE_JMES


# @cv.task_schema(
#     {
#         vol.Exclusive("jmespath", "XOR"): vol.All(cv.ensure_list, [cv.isjmespath]),
#         vol.Exclusive("template", "XOR"): cv.templateSchema(object),
#     },
#     target=1,
#     tables=(0, 0),
#     kwargs=True,
# )
# def task_template(table, jmespath=None, template=None):
#     """Execute a jmespath expression on a table."""
#     if jmespath:
#         jmespath = " | ".join(jmespath)
#         res = process_template_str(f"{TEMPLATE_JMES} {jmespath}", table)
#         if res == "":
#             logging.getLogger(__name__).error("Empty template expansion: %s", jmespath)
#         return res
#     if template:
#         return template
#     return None


# @cv.task_schema({cv.slug: cv.templateSchema()}, target=0, tables=(0, 0))
# def task_vars(env, opt):
#     """Set a variable."""
#     for key, val in opt.items():
#         env.var[key] = val
