from odoo import models
import io
import xlsxwriter
import base64
from datetime import datetime


class ReportSoPackageDifference(models.AbstractModel):
    _name = 'report.visio_tti_so_customize.so_package_difference_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        print("generating report")
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        worksheet = workbook.add_worksheet('Package Difference')
        bold_center = workbook.add_format({'bold': True, 'align': 'center'})
        sale_order_name = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 16, 'bg_color': '#1F4E78',
                                               'font_color': 'white', })
        pckg_name = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 12, 'bg_color': '#1F4E78',
                                               'font_color': 'white', 'border':1 })
        header = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'align': 'center' , 'border':1})
        cell = workbook.add_format({'align': 'center','text_wrap':False,'valign': 'top', 'shrink': True})
        row = 2

        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to)]
        orders = self.env['sale.order'].search(domain)
        print("orders" , len(orders))
        for order in orders:
            package_lines = order.order_line.filtered(lambda l: l.test_type == 'test_package')
            print("pkg lines", len(package_lines))
            if not package_lines:
                continue

            mismatch_found = False
            order_buffer = []  # hold package sections

            for pkg_line in package_lines:
                package = pkg_line.product_id
                expected_tests = package.product_tmpl_id.test_report_ids
                actual_tests = order.tti_test_report_line_ids.filtered(lambda l: l.package_id.id == package.id)
                print("expected tests" , expected_tests)
                print("expected tests" , len(expected_tests))
                print("actual tests" , actual_tests)
                print("actual tests" , len(actual_tests))
                mismatch_rows = []

                for expected in expected_tests:
                    actual = actual_tests.filtered(lambda x: x.test_report.id == expected.test_report.id)
                    if not actual:
                        mismatch_rows.append((
                            expected.test_report.display_name,
                            expected.qty,
                            expected.total_cost,
                            '', 0, 0
                        ))
                        mismatch_found = True
                        continue

                    actual = actual[0]
                    if actual.qty != expected.qty or actual.list_price != expected.total_cost:
                        mismatch_rows.append((
                            expected.test_report.display_name,
                            expected.qty,
                            expected.total_cost,
                            actual.test_report.name,
                            actual.qty,
                            actual.list_price
                        ))
                        mismatch_found = True

                print("mismatched rows " , mismatch_rows)
                print("mismatched rows " , len(mismatch_rows))
                if mismatch_rows:
                    order_buffer.append((package.name, mismatch_rows))

            if not mismatch_found:
                continue  # ❗ skip sale order if no mismatches found in any package

            worksheet.merge_range(row, 2, row, 8, f"{order.name}", sale_order_name)
            row += 2
            print("orders buffer " , order_buffer)

            for pkg_name, mismatch_rows in order_buffer:
                worksheet.merge_range(row, 3, row, 7, f"{pkg_name}", pckg_name)
                row += 1

                # Section Headers
                worksheet.merge_range(row, 4, row, 5 ,"Original Test", header)
                worksheet.merge_range(row, 6, row, 7 ,"SO Test", header)
                row += 1

                # Column headers under each section
                worksheet.write(row, 3, "Test Name", header)
                worksheet.set_column(3, 3, 50)
                worksheet.write(row, 4, "Qty", header)
                worksheet.write(row, 5, "Price", header)
                worksheet.write(row, 6, "Qty", header)
                worksheet.write(row, 7, "Price", header)
                row += 1

                # Actual data rows
                for test_name, ex_qty, ex_price, act_name, act_qty, act_price in mismatch_rows:
                    worksheet.write(row, 3, test_name, cell)
                    worksheet.write(row, 4, ex_qty, cell)
                    worksheet.write(row, 5, ex_price, cell)
                    worksheet.write(row, 6, act_qty, cell)
                    worksheet.write(row, 7, act_price, cell)
                    worksheet.set_row(row, 22)
                    row += 1

                row += 2  # spacing between packages


