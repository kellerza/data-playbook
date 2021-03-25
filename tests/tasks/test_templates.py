# """Tests for jmespath.py"""
# import pytest
# import voluptuous as vol

# import dataplaybook.config_validation as cv
# from dataplaybook import DataPlaybook

# # pylint: disable=no-member


# @cv.task_schema({}, target=1, kwargs=True)
# def task_load_test_data(env=None):
#     """Load test data."""
#     return [
#         {'k': 1, 'v': 'one'},
#         {'k': 2, 'v': 'two'},
#         {'k': '2', 'v': 'two string'},
#     ]


# def test_jmespath_task():
#     """Test basic jmespath to variable."""
#     dpb = DataPlaybook(modules=__name__, yaml_text="""
#         modules: [dataplaybook.tasks.templates]
#         tasks:
#           - task: load_test_data
#             target: test

#           - task: template
#             jmespath: "test[?k==`2`].v | [0]"
#             target: test2

#           - task: template
#             jmespath: "test[?k==`2`].v"
#             target: test3

#           - task: template
#             jmespath: "test[?k=='2'].v"
#             target: test_str

#           - task: template
#             jmespath: "test[?k=='2'].v"
#             target: test_str2

#           - template:
#               jmespath: "test[?k=='2'].v"
#             target: test_str3
#         """)
#     dpb.run()
#     assert dpb.tables['test'][0] == {'k': 1, 'v': 'one'}
#     assert dpb.tables.var == {'test2': 'two'}
#     assert dpb.tables.var.test2 == 'two'

#     assert dpb.tables['test3'] == ['two']

#     assert dpb.tables['test_str'] == ['two string']
#     assert dpb.tables['test_str2'] == ['two string']
#     assert dpb.tables['test_str3'] == ['two string']


# def test_templateSchema_jmespath():  # pylint: disable=invalid-name
#     """Test basic jmespath to variable."""
#     dpb = DataPlaybook(modules=__name__, yaml_text="""
#         modules: [dataplaybook.tasks.templates]
#         tasks:
#           - task: load_test_data
#             target: test

#           - vars:
#               test1: Normal return value
#               test2: jmespath test[?k==`2`].v | [0]
#     """)
#     dpb.run()
#     assert dpb.tables['test'][0] == {'k': 1, 'v': 'one'}
#     assert dpb.tables.var.test1 == 'Normal return value'
#     assert dpb.tables.var.test2 == 'two'


# def test_templateSchema_jinja():  # pylint: disable=invalid-name
#     """Test basic jinja to variable."""
#     dpb = DataPlaybook(modules=__name__, yaml_text="""
#         modules: [dataplaybook.tasks.templates]
#         tasks:
#           - task: load_test_data
#             target: test

#           - vars:
#               test1: Normal return value
#               test0: '{{ test[0].v }}'

#           - template:
#               template: '{{ test[1].v }}'
#             target: test2
#     """)
#     dpb.run()
#     assert dpb.tables['test'][0] == {'k': 1, 'v': 'one'}
#     assert dpb.tables.var.test1 == 'Normal return value'
#     assert dpb.tables.var.test0 == 'one'
#     assert dpb.tables.var.test2 == 'two'

#     with pytest.raises(vol.Invalid):
#         dpb.execute_task(
#             {'template': {'template': 'a', 'jmespath': 'test[1]'}}
#         )


# def test_templateSchema_readme_example():  # pylint: disable=invalid-name
#     """Tests for readme examples."""
#     dpb = DataPlaybook(modules=__name__, yaml_text="""
#         modules: [dataplaybook.tasks, dataplaybook.tasks.templates]
#         tasks:
#           - load_test_data: {}
#             target: test

#           - template:
#               jmespath: "test[?k=='2'].v | [0]"
#             target: task_1_result

#           - vars:
#               task_2_result: "{{ test | selectattr('k', 'equalto', '2') | map(attribute='v') | first }}"

#           - build_lookup_var:
#               key: k
#               columns: [v]
#             tables: test
#             target: lookup1

#           - vars:
#               task_3_result: "{{ var['lookup1']['2'].v }}"


#     """)  # noqa
#     dpb.run()

#     twos = 'two string'
#     assert dpb.tables.var.task_1_result == twos
#     assert dpb.tables.var.task_2_result == twos
#     assert dpb.tables.var.task_3_result == twos


# def test_jmespath_custom_to_table_dict():
#     """Test to_table."""
#     dpb = DataPlaybook(modules='dataplaybook.tasks.templates')
#     dpb.tables['test'] = {
#         'a': {'v': 1},
#         'b': {'v': {'v2': 2}},
#     }
#     dpb.execute_task({
#         'template': {
#             'jmespath': "test | to_table(@, 'key')"
#         },
#         'target': 'test2'
#     })
#     assert dpb.tables['test2'] == [
#         {'key': 'a', 'v': 1},
#         {'key': 'b', 'v': {'v2': 2}}
#     ]


# def test_jmespath_custom_to_table_list():
#     """Test to_table."""
#     dpb = DataPlaybook(modules='dataplaybook.tasks.templates')
#     dpb.tables['test'] = [
#       {'id': 1, 'key': {
#           'a': {'v': 1},
#           'b': {'v': {'v2': 2}},
#       }},
#       {'id': 2, 'key': {
#           'a': {'v': 3},
#           'b': {'v': {'v2': 4}},
#       }},
#     ]
#     dpb.execute_task({
#         'template': {
#             'jmespath': "test | to_table(@, 'key')"
#         },
#         'target': 'test2'
#     })
#     assert dpb.tables['test2'] == [
#         {'id': 1, 'key': 'a', 'v': 1},
#         {'id': 1, 'key': 'b', 'v': {'v2': 2}},
#         {'id': 2, 'key': 'a', 'v': 3},
#         {'id': 2, 'key': 'b', 'v': {'v2': 4}}
#     ]


# def test_jmespath_custom_flatten():
#     """Test to_table."""
#     dpb = DataPlaybook(modules='dataplaybook.tasks.templates')
#     dpb.tables['test'] = [
#         {'key': 'a', 'v': 1},
#         {'key': 'b', 'v': {'v2': {'v3': {'v4': 4}}}}
#     ]

#     dpb.execute_task({
#         'template': {
#             'jmespath': "test | flatten(@, `1`)"
#         },
#         'target': 'test1'
#     })
#     dpb.execute_task({
#         'template': {
#             'jmespath': "test | flatten(@, `2`)"
#         },
#         'target': 'test2'
#     })
#     dpb.execute_task({
#         'template': {
#             'jmespath': "test | flatten(@, `3`)"
#         },
#         'target': 'test3'
#     })

#     assert dpb.tables['test1'] == [
#         {'key': 'a', 'v': 1},
#         {'key': 'b', 'v_v2': {'v3': {'v4': 4}}}
#     ]
#     assert dpb.tables['test2'] == [
#         {'key': 'a', 'v': 1},
#         {'key': 'b', 'v_v2_v3': {'v4': 4}}
#     ]
#     assert dpb.tables['test3'] == [
#         {'key': 'a', 'v': 1},
#         {'key': 'b', 'v_v2_v3_v4': 4}
#     ]
