import tabula
from fuzzywuzzy import fuzz
from pandas import DataFrame
from typing import Union, List, Dict, Tuple


# This class reads a PDF file and separates the tables into groups.
# The tables are stored in a dictionary where the key is the table group name.
# The value is a list of dataframes.
#
# The table groups are:
# Introduction
# Configuration
# Specification
# Accessories
#
# This class offers methods so that TabulaPy manipulation is abstracted away.
class ChevroletPDFReader:
    INTRODUCTION_GROUP = 'Introduction'
    CONFIGURATION_GROUP = 'Configuration'
    SPECIFICATION_GROUP = 'Specification'
    ACCESSORIES_1_GROUP = 'Accessories'
    ACCESSORIES_2_GROUP = 'Accessories 2'
    _TABLE_GROUP_NAMES = [INTRODUCTION_GROUP, CONFIGURATION_GROUP, SPECIFICATION_GROUP, ACCESSORIES_1_GROUP, ACCESSORIES_2_GROUP]

    def __init__(self, filename):
        # Read all tables from the PDF file.
        dataframes = tabula.read_pdf(filename, pages='all', lattice=True, multiple_tables=True)
        # Call the initial setup method.
        self._initial_setup(dataframes)

    # This method separates the tables into groups and sanitizes the dataframes.
    def _initial_setup(self, dataframes) -> None:
        # Map of tables by group.
        self._tables_by_group: Dict[str, List[DataFrame]] = {}
        for table_group in self._TABLE_GROUP_NAMES:
            self._tables_by_group[table_group] = []
        # Variable to keep track of the current table group.
        current_table_group_index = 0
        # Removing new lines from column names and removing unnamed columns.
        # Also removing empty dataframes.
        for dataframe in dataframes:
            table_group = self._TABLE_GROUP_NAMES[current_table_group_index]
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
                table_group = self._TABLE_GROUP_NAMES[current_table_group_index]
                self._tables_by_group[table_group].append(dataframe)

    # This is a very complex method, which will be explained below:
    #
    # This method basically returns the value of a cell in a table.
    # However, this method is very flexible and can be used in many ways:
    #
    # Two parameters are always the same:
    #
    # table_group: str => The table group name.
    # table_index: int => The table index (position) in the table group.
    #
    # The last two parameters can be used in two ways:
    #
    # column_index_or_name: int OR str => The column index or the column name.
    # line_number_or_name: int OR Tuple[int, str] => The line number or a tuple (column_number, line_name).
    #
    # The column_index_or_name parameter can be an integer or a string. If it is an integer, it will be used as the
    # column index. If it is a string, it will be used as the column name. Column names are matched using fuzzywuzzy
    # (fuzzy string matching).
    #
    # The line_number_or_name parameter can be an integer or a tuple (column_number, line_name). If it is an integer,
    # it will be used as the line number. If it is a tuple, it will be used as a tuple (column_number, line_name).
    # Line names are also matched using fuzzywuzzy.
    def get_column_value(self, table_group: str, table_index: int, column_index_or_name: Union[int, str],
                         line_number_or_name: Union[int, Tuple[int, str]]):
        # Return empty string if the table group doesn't exist.
        if table_group not in self._tables_by_group:
            return ''
        # Return empty string if the table index is out of range.
        if table_index >= len(self._tables_by_group[table_group]):
            return ''
        table = self._tables_by_group[table_group][table_index]
        # Which column to use?
        # Should we use the column name or the column index?
        # It depends on the type of the column_index_or_name parameter (int or str).
        column_index = 0
        # If using column name...
        if isinstance(column_index_or_name, str):
            # Using fuzzywuzzy to find the most similar column name.
            most_similar_column_index = 0
            most_similar_column_ratio = 0
            for index, name in enumerate(table.columns):
                ratio = fuzz.ratio(str.lower(name), str.lower(column_index_or_name))
                if ratio >= 75 and ratio > most_similar_column_ratio:
                    most_similar_column_index = index
                    most_similar_column_ratio = ratio
            column_index = most_similar_column_index
        # If using column index...
        elif isinstance(column_index_or_name, int):
            column_index = column_index_or_name
        else:
            return ''
        # Ok, now we have the column index.
        # Now, should we use the line number or a tuple (column_number, line_name)?
        # It depends on the type of the line_number_or_name parameter (int or Tuple[int, str]).
        # If using line number...
        if isinstance(line_number_or_name, int):
            if line_number_or_name >= len(table):
                return ''
            return table.iloc[line_number_or_name, column_index]
        # If using tuple (column_number, line_name)...
        elif isinstance(line_number_or_name, Tuple):
            # Using fuzzywuzzy to find the most similar line name.
            most_similar_line_index = 0
            most_similar_line_ratio = 0
            column_number = line_number_or_name[0]
            line_name = line_number_or_name[1]
            for index, name in enumerate(table.iloc[:, column_number]):
                ratio = fuzz.ratio(str.lower(name), str.lower(line_name))
                if ratio >= 75 and ratio > most_similar_line_ratio:
                    most_similar_line_index = index
                    most_similar_line_ratio = ratio
            if most_similar_line_ratio == 0:
                return ''
            return table.iloc[most_similar_line_index, column_index]
        else:
            return ''
        pass


# Instantiate the reader.
reader = ChevroletPDFReader('carros.pdf')

# Example 1: Get the value of the cell in the 'Marca/Modelo' column in the first line of the first table in the
# 'Introduction' group.
value_1 = reader.get_column_value(ChevroletPDFReader.INTRODUCTION_GROUP, 0, 'Marca/Modelo', 0)
print(f"Value 1: {value_1}")

# Example 2: Get the value of the cell in the first column, in the first line of the second table in the
# 'Introduction' group.
value_2 = reader.get_column_value(ChevroletPDFReader.INTRODUCTION_GROUP, 1, 0, 0)
print(f"Value 2: {value_2}")

value_3 = reader.get_column_value(ChevroletPDFReader.CONFIGURATION_GROUP, 0, 0, 0)
print(f"Value 3: {value_3}")

# Using the first configuration table, check if the 'LT Turbo 116cv' configuration has the 'Brake Light' option.
# This is done by checking if the value of the cell in the 'LT Turbo 116cv' column in the 'Brake Light' line is
# a X or not.
value_4 = reader.get_column_value(ChevroletPDFReader.CONFIGURATION_GROUP, 0, 'LT Turbo 116cv', (0, 'Brake Light'))
print(f"Value 4: {value_4}")
