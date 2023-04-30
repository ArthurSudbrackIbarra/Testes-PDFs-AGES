import pdfplumber
from fuzzywuzzy import fuzz
from typing import Dict, List


# Method that uses Fuzzy string matching to check if two strings are similar.
# str1: First string to be compared.
# str2: Second string to be compared.
# ratio (optional): Minimum ratio of similarity between the two strings.
def is_similar(str1, str2, ratio: int = 75):
    return fuzz.ratio(str.lower(str1), str.lower(str2)) >= ratio


# JeepPDFReader class that reads a PDF file and extracts the data from it.
# file_path: Path to the PDF file.
class JeepPDFReader:
    # Constants used to extract the data from the PDF file.
    # They are used to check for patterns in the PDF file.
    COLUMN_NAMES_STRING_MATCH = "MVS MY DESCRIÇÃO COMB. PREÇO(R$) PÁGINA"
    TABLE_FOOTER_STRING_MATCH = "Tabela temporária e provisória, sujeita a modificações diárias. Para uso exclusivo e " \
                                "simples consulta por parte do profissional vendedor, não gerando obrigações de venda " \
                                "pelos valores meramente indicativos. "
    POSSIBLE_FUEL_TYPES = ['flex', 'diesel', 'gasolina']

    # Constructor of the class.
    def __init__(self, file_path: str):
        self.file_path: str = file_path
        self.cars: Dict[str, Dict[str, str]] = {}
        self.column_names: List[str] = []
        self._initial_setup()

    # Method that reads the PDF file and extracts the data from it.
    # It is called by the constructor.
    # It fills the 'cars' dictionary with the data extracted from the PDF file.
    # The dictionary has the following structure:
    # {
    #   'sigla': {
    #       'MVS': '...',
    #       'MY': '...',
    #       'DESCRIÇÃO': '...',
    #       'COMB.': '...',
    #       'PREÇO(R$)': '...',
    #       'PÁGINA': '...'
    #   },
    #   ...
    def _initial_setup(self):
        with pdfplumber.open(self.file_path) as pdf:
            pages = pdf.pages
            reading_cars = False
            # Iterates through the pages of the PDF file.
            for page in pages:
                page_content = page.extract_text()
                # print(page_content)
                lines = page_content.split('\n')
                # Iterates through the lines of the page.
                for line in lines:
                    # If in the process of reading the cars (first table)...
                    if reading_cars:
                        # Creating the car_data_parsed list.
                        # This list will contain the data of the car.
                        # The name of the car might contain spaces, and when split by spaces, it will be split into
                        # multiple elements. We have to join these elements back together.
                        # Car data not parsed yet.
                        car_data = line.split(' ')
                        # Car data from positions 3 to the end (CAR NAME PARTS, FUEL TYPE, PRICE and PAGE)
                        card_data_sub = car_data[2:]
                        # Car data from positions 0 to 2. (MVS, MY and DESCRIÇÃO)
                        car_data_parsed = car_data[:3]
                        # Car data parsed with the car name joined back together.
                        car_data_parsed[-1] = ''
                        # Index where the fuel type is located.
                        fuel_type_index = -1
                        for i in range(len(card_data_sub)):
                            data = card_data_sub[i]
                            # If the data is a fuel type, the car name has ended.
                            # Break the for loop.
                            if str.lower(data) in JeepPDFReader.POSSIBLE_FUEL_TYPES:
                                car_data_parsed.append(data)
                                fuel_type_index = i + 1
                                break
                            # If the data is not a fuel type, it is part of the car name.
                            # Join it back together in the last element of the car_data_parsed list.
                            else:
                                car_data_parsed[-1] += ' ' + data
                        # Append the rest of the data to the car_data_parsed list.
                        car_data_parsed += card_data_sub[fuel_type_index:]
                        # Get the 'sigla', which is the key of the car in the dictionary.
                        sigla = car_data[0]
                        # If the 'sigla' is valid and the line is not the table footer...
                        # It means that we still have cars to process.
                        if len(sigla) == 7 and not is_similar(line, JeepPDFReader.TABLE_FOOTER_STRING_MATCH):
                            self.cars[sigla] = {}
                            for i in range(len(self.column_names)):
                                self.cars[sigla][self.column_names[i]] = car_data_parsed[i]
                        else:
                            # If the 'sigla' is not valid or the line is the table footer...
                            # It means that we have finished processing the cars.
                            # Set the 'reading_cars' flag to False.
                            reading_cars = False
                    # If not in the process of reading the cars...
                    elif is_similar(line, JeepPDFReader.COLUMN_NAMES_STRING_MATCH):
                        self.column_names = line.split(' ')
                        reading_cars = True

    # Method that returns the cars extracted from the PDF file.
    # It returns a copy of the dictionary, so that the original dictionary is not modified.
    def get_cars(self) -> Dict[str, Dict[str, str]]:
        return self.cars.copy()


# Testing the class.
reader = JeepPDFReader('jeep2.pdf')
cars = reader.get_cars()
print(cars)
