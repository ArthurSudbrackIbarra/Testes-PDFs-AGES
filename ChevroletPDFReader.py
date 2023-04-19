import tabula
from fuzzywuzzy import fuzz

TABLE_GROUP_NAMES = ['Introduction', 'Configuration', 'Specification', 'Accessories']


class ChevroletPDFReader:
    def __init__(self, filename):
        dataframes = tabula.read_pdf(filename, pages='all', lattice=True, multiple_tables=True)
        # All tables.
        self._tables = []
        # Map of tables by group.
        self._tables_by_group = {}
        for table_group in TABLE_GROUP_NAMES:
            self._tables_by_group[table_group] = []
        # Variable to keep track of the current table group.
        current_table_group_index = 0
        # Removing new lines from column names and removing unnamed columns.
        # Also removing empty dataframes.
        # The sanitized dataframes are appended to the _tables list.
        for dataframe in dataframes:
            table_group = TABLE_GROUP_NAMES[current_table_group_index]
            if dataframe.empty:
                continue
            for column in dataframe.columns:
                dataframe.rename(columns={column: column.replace('\r', ' ')}, inplace=True)
                if 'unnamed' in str.lower(column):
                    del dataframe[column]
            if len(dataframe.columns) <= 1:
                continue
            self._tables.append(dataframe)
            # Is the current table of the same group as the previous one?
            # Or is it a completely new group?
            if len(self._tables_by_group[table_group]) == 0:
                self._tables_by_group[table_group].append(dataframe)
            else:
                # Check if the current table is of the same group as the previous one.
                # To do that, check if all columns are the same or if the number of columns is different.
                previous_table = self._tables_by_group[table_group][-1]
                if len(previous_table.columns) != len(dataframe.columns):
                    current_table_group_index += 1
                    self._tables_by_group[table_group].append(dataframe)
                else:
                    # Check if all columns are the same.
                    same_columns = True
                    for column in previous_table.columns:
                        if column not in dataframe.columns:
                            same_columns = False
                            break
                    if not same_columns:
                        # Change the current table group.
                        current_table_group_index += 1
                    table_group = TABLE_GROUP_NAMES[current_table_group_index]
                    self._tables_by_group[table_group].append(dataframe)

    # This method returns the value of a column in a table.
    # The table group is the name of the table group.
    # The table index is the index of the table in the table group.
    # The column name is the name of the column.
    # The column line is the line of the column.
    def get_column_value(self, table_group, table_index, column_name, column_line) -> str:
        if table_group not in self._tables_by_group:
            return ""
        if table_index >= len(self._tables_by_group[table_group]):
            return ""
        table = self._tables_by_group[table_group][table_index]
        # Using fuzzywuzzy to find the most similar column name.
        for column in table.columns:
            if fuzz.ratio(str.lower(column), str.lower(column_name)) >= 75:
                if column_line >= len(table[column]):
                    return ""
                return table[column][column_line]


reader = ChevroletPDFReader('carros.pdf')
value = reader.get_column_value('Introduction', 0, 'CODIGO VENDAS', 2)
print(value)
