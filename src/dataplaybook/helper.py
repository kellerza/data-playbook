"""Helper functions."""

from operator import itemgetter


# Source:
# https://www.calazan.com/
#     python-function-for-displaying-a-list-of-dictionaries-in-table-format/
def format_as_table(
    data: list,
    keys: list,
    header: list[str] | None = None,
    sort_by_key: str | None = None,
    sort_order_reverse: bool = False,
) -> str:
    """Text formatted table from a list of dicts.

    Required Parameters:
        data - Data to process (list of dictionaries). (Type: List)
        keys - List of keys in the dictionary. (Type: List)

    Optional Parameters:
        header - The table header. (Type: List)
        sort_by_key - The key to sort by. (Type: String)
        sort_order_reverse - Default sort order is ascending, if
            True sort order will change to descending. (Type: Boolean)
    """
    # Sort the data if a sort key is specified (default sort order
    # is ascending)
    if sort_by_key:
        data = sorted(data, key=itemgetter(sort_by_key), reverse=sort_order_reverse)

    # If header is not empty, add header to data
    if header:
        # Get the length of each header and create a divider based
        # on that length
        header_divider = []
        for name in header:
            header_divider.append("-" * len(name))

        # Create a list of dictionary from the keys and the header and
        # insert it at the beginning of the list. Do the same for the
        # divider and insert below the header.
        data.insert(0, dict(zip(keys, header_divider, strict=False)))
        data.insert(0, dict(zip(keys, header, strict=False)))

    column_widths = []
    for key in keys:
        column_widths.append(max(len(str(column[key])) for column in data))

    # Create a tuple pair of key and the associated column width for it
    key_width_pair = zip(keys, column_widths, strict=False)

    fmt = ("{} " * len(keys)).strip() + "\n"
    #   = ("%-*s ' * len(keys)).strip() + '\n'
    formatted_data = ""
    for element in data:
        data_to_format = []
        # Create a tuple that will be used for the formatting in
        # width, value format
        for pair in key_width_pair:
            data_to_format.append((pair[1], element[pair[0]]))
        print(fmt)
        print(data_to_format)
        if data_to_format:
            formatted_data += fmt.format(*data_to_format)
    return formatted_data
