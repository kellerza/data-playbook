"""Fuzzy matching."""

from fuzzywuzzy import fuzz

from dataplaybook import RowData, task


@task
def fuzzy_match(
    *,
    table1: list[RowData],
    table2: list[RowData],
    t1_column: str,
    t2_column: str,
    t1_target_column: str,
) -> None:
    """Fuzzy matching.

    https://marcobonzanini.com/2015/02/25/fuzzy-string-matching-in-python/
    """
    t2_colname = t2_column
    t2_names = list({str(r[t2_colname]) for r in table2 if r.get(t2_colname)})
    t2_namesl = list(map(str.lower, t2_names))

    for row in table1:
        col1 = row.get(t1_column)
        if not col1:
            continue
        col1 = str(col1).lower()
        # res = process.extractBests(
        #     col1, t2_names, limit=10, scorer=fuzz.ratio)
        # row[opt.target_column] = '' if not res else res[0][0]
        # row[opt.target_column + '#'] = 0 if not res else res[0][1]
        # row[opt.target_column + '_'] = str(res)

        res = []
        for col2l, col2 in zip(t2_namesl, t2_names, strict=False):
            resf = fuzz.ratio(col1, col2l)
            if resf > 20:
                res.append((resf, col2))
        res.sort(key=lambda rec: rec[0], reverse=True)
        row[t1_target_column] = "" if not res else res[0][1]
        row[t1_target_column + "#"] = 0 if not res else res[0][0]
        row[t1_target_column + "_"] = str(res[:10])
