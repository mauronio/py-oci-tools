import xlsxwriter
import os

from base_writer import ReportWriter

class SpreadSheetWriter(ReportWriter):

    def __init__(self, working_path, config):

        super().__init__(working_path, config)

        self.settings = config['spreadsheet-settings']
        self.workbook = xlsxwriter.Workbook(os.path.join(working_path, self.settings['file-name']))
        self.bold_format = self.workbook.add_format({'bold': True})
        self.title_format = self.workbook.add_format()
        self.title_format.set_font_size(11)
        self.title_format.set_bold()
        self.default_format = self.workbook.add_format()
        self.default_format.set_border(1)
        self.default_format.set_font_size(9)
        self.header_format = self.workbook.add_format()
        self.header_format.set_font_size(9)
        self.header_format.set_top(2)
        self.header_format.set_top_color('red')
        self.header_format.set_bold()
        self.current_coordinates = {}
        for report in config['reports']:
            report_name = report['name']
            self.workbook.add_worksheet(report_name)
            self.current_coordinates[report_name] = self.settings['start-coordinates'].copy()


    def write_table(self, report_name, title, column_list, row_list):

        current_coordinates = self.current_coordinates[report_name]
        worksheet = self.workbook.get_worksheet_by_name(report_name)
        worksheet.hide_gridlines(2)

        row = current_coordinates['row']
        col = current_coordinates['col']

        worksheet.write(row, col, title, self.title_format)
        row += 1

        for column in column_list:
            column_name = column['name']
            worksheet.write(row, col, column_name, self.header_format)
            col += 1 

        row += 1
        col = current_coordinates['col']

        for row_data in row_list:
            col = current_coordinates['col']
            for col_data in row_data:
                worksheet.write(row, col, col_data, self.default_format)
                col += 1
            row += 1 

        row += 1 

        current_coordinates['row'] = row
        
    def close(self):

        self.workbook.close()

