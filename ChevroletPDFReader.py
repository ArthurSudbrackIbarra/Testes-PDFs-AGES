import tabula
from fuzzywuzzy import fuzz

TABLE_GROUP_NAMES = ['Introduction', 'Configuration', 'Specification', 'Accessories']


class ChevroletPDFReader:
    def __init__(self, filename):
        # Read all tables from the PDF file.
        dataframes = tabula.read_pdf(filename, pages='all', lattice=True, multiple_tables=True)
        # Call the initial setup method.
        self._initial_setup(dataframes)

    # This method separates the tables into groups and sanitizes the dataframes.
    def _initial_setup(self, dataframes) -> None:
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
            # Don't consider empty tables.
            if dataframe.empty:
                continue
            for column in dataframe.columns:
                # Remove new lines from column names.
                dataframe.rename(columns={column: column.replace('\r', ' ')}, inplace=True)
                # Remove unnamed columns.
                if 'unnamed' in str.lower(column):
                    del dataframe[column]
            # Don't consider tables with only one column.
            if len(dataframe.columns) <= 1:
                continue
            # Is the current table of the same group as the previous one?
            # Or is it a completely new group?
            if len(self._tables_by_group[table_group]) == 0:
                self._tables_by_group[table_group].append(dataframe)
            else:
                # Check if the current table is of the same group as the previous one.
                # To do that, check if the number of columns is the same and if the columns are the same.
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
                        # Increment the current table group index.
                        # This is to change the current table group from now on.
                        current_table_group_index += 1
                    # Append the table to the current table group.
                    table_group = TABLE_GROUP_NAMES[current_table_group_index]
                    self._tables_by_group[table_group].append(dataframe)

    # This method returns the value of a column in a table.
    # The table group is the name of the table group.
    # The table index is the index of the table in the table group.
    # The column name is the name of the column.
    # The column line is the line of the column.
    def get_column_value(self, table_group: str, table_index: int, column_name: str, column_line: int) -> str:
        # Return empty string if the table group doesn't exist.
        if table_group not in self._tables_by_group:
            return ""
        # Return empty string if the table index is out of range.
        if table_index >= len(self._tables_by_group[table_group]):
            return ""
        table = self._tables_by_group[table_group][table_index]
        # Using fuzzywuzzy to find the most similar column name.
        chosen_column = ''
        chosen_column_ratio = 0
        for column in table.columns:
            ratio = fuzz.ratio(str.lower(column), str.lower(column_name))
            if ratio >= 75 and ratio > chosen_column_ratio:
                chosen_column = column
                chosen_column_ratio = ratio
        # Return empty string if the column name doesn't exist.
        if column_line >= len(table[chosen_column]):
            return ""
        # Return the value of the column.
        return table[chosen_column][column_line]


reader = ChevroletPDFReader('carros.pdf')
value = reader.get_column_value('Configuration', 0, 'AT Turbo 116cv', 0)
print(value)
