"""Scripts to extract the Dcitionary data from the input XLSX/CSV file to an md format"""

import pandas as pd

strong_col = 'Strongs'
data_col = 'BDB / Thayers'

class ProcessDictionary:
    def __init__(self,
                 filepath, excel_sheet, header_row, output_folder="output"):
        self.bsb_df = pd.read_excel(filepath, sheet_name=excel_sheet, header=header_row)

        self.dictionary = {}
        self.bsb_df.apply(lambda row: self.row2dictionary(row), axis=1)
        self.dictionary = dict(sorted(self.dictionary.items()))
        self.save_output_file(output_folder)

    def row2dictionary(self, row):
    	try:
    		if not pd.isna(row[strong_col]):
    			strong_num = f"{row['Language'][0].upper()}{int(row[strong_col])}" 
    			if strong_num not in self.dictionary:
    				self.dictionary[strong_num] = row[data_col]
    	except Exception as exce:
    		print(f"Issue at {row=}")
    		print(exce)

    def save_output_file(self, output_folder):
    	with open(f"{output_folder}/Strongs_dictionary.md", 'w', encoding='utf-8') as dict_file:
    		dict_file.write("# Strongs Dictionary\n")
    		for item in self.dictionary:
    			dict_file.write(f"\n## {item}\n")
    			dict_file.write(f"{self.dictionary[item]}\n")

if __name__== '__main__':
    input_excel = 'input/bsb_tables.xlsx'
    excel_sheet = 'biblosinterlinear96'
    header_row = 1
    output_folder = 'output/'
    ProcessDictionary(input_excel, excel_sheet, header_row, output_folder)
        