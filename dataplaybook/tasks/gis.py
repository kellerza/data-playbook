"""GIS / QGIS tasks."""
import voluptuous as vol

import dataplaybook.config_validation as cv


@cv.task_schema({
    vol.Optional('latA', default='latA'): cv.col_use,
    vol.Optional('latB', default='latB'): cv.col_use,
    vol.Optional('lonA', default='lonA'): cv.col_use,
    vol.Optional('lonB', default='lonB'): cv.col_use,
    vol.Optional('error', default='22 -22'): str,
    vol.Optional('linestring', default='linestring'): cv.col_add,
}, tables=1)
def task_linestring(table, opt):
    """Add a linestring column to a table."""
    for row in table:
        try:
            lla = "{:4d} {:4d}".format(
                row[opt.lonA], row[opt.latA])
        except IndexError:
            lla = opt.error

        try:
            llb = "{:4d} {:4d}".format(
                row[opt.lonB], row[opt.latB])
        except IndexError:
            llb = opt.error

        row[opt.linestring] = "linestring({}, {})".format(lla, llb)
