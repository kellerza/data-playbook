"""GIS / QGIS tasks."""

from dataplaybook import RowData, task


@task
def linestring(
    *,
    table: list[RowData],
    lat_a: str = "latA",
    lat_b: str = "latB",
    lon_a: str = "lonA",
    lon_b: str = "lonB",
    linestring_column: str = "linestring",
    error: str = "22 -22",
) -> list[RowData]:
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
