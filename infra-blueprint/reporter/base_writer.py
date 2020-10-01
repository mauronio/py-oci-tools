class ReportWriter:

    def __init__(self, working_path, config):
         print('Writing to', config['spreadsheet-settings']['file-name'])

    def write_table(self, report_name, title, column_list, row_list):
         raise NotImplementedError("The method not implemented")

    def close(self):
         raise NotImplementedError("The method not implemented")
