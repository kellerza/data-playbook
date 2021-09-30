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
            lla = f"{row[lon_a]:4d} {row[lat_a]:4d}"
        except IndexError:
            lla = error

        try:
            llb = f"{row[lon_b]:4d} {row[lat_b]:4d}"
        except IndexError:
            llb = error

        row[linestring_column] = f"linestring({lla}, {llb})"
    return table
