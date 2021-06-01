"""GIS / QGIS tasks."""
from dataplaybook import Table, task


@task
def linestring(
    table: Table,
    lat_a: str = "latA",
    lat_b: str = "latB",
    lon_a: str = "lonA",
    lon_b: str = "lonB",
    linestring_column: str = "linestring",
    error: str = "22 -22",
) -> Table:
    """Add a linestring column to a table."""
    for row in table:
        try:
            lla = "{:4d} {:4d}".format(row[lon_a], row[lat_a])
        except IndexError:
            lla = error

        try:
            llb = "{:4d} {:4d}".format(row[lon_b], row[lat_b])
        except IndexError:
            llb = error

        row[linestring_column] = "linestring({}, {})".format(lla, llb)
