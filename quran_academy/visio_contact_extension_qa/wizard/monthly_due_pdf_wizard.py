# quran_academy/visio_contact_extension_qa/wizard/monthly_due_pdf_wizard.py
from datetime import datetime, time, date
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import base64
import io
import xlsxwriter



class MonthlyDuePdfWizard(models.TransientModel):
    _name = 'monthly.due.pdf.wizard'
    _description = 'Monthly Due PDF Wizard'


    date_from = fields.Date(string='Date From', required=True)
    date_to   = fields.Date(string='Date To',   required=True)

    # small sanity-check
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise ValidationError("'Date From' must be on or before 'Date To'.")

    def _months_between(self):
        """Full calendar months between the two dates (inclusive)."""
        self.ensure_one()
        d1, d2 = self.date_from, self.date_to
        delta  = relativedelta(d2, d1)
        return delta.years * 12 + delta.months + 1

    def _get_due_lines(self):
        self.ensure_one()
        months = self._months_between()

        # display values → first letter
        g_map = {'male': 'M', 'female': 'F', 'other': 'O'}

        partners = self.env['res.partner'].sudo().search([])
        lines = []
        for p in partners:
            lines.append({
                'ac_num': p.ac_numnber_qa or '',
                'gender': g_map.get(p.gender_qa, ''),
                'name': p.name or '',
                'mobile': p.mobile or '',
                'mem_date': p.mem_date,
                'paid_upto': p.trans_date_qa,
                'months': months,
                'mlcontb': p.mlcontb or 0,
                'dues': months * (p.mlcontb or 0),
            })
        return lines

    def action_generate_pdf(self):
        self.ensure_one()
        return self.env.ref(
            'visio_contact_extension_qa.action_monthly_due_report'
        ).report_action(self, data={})

    def action_generate_excel(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Monthly Due Report')

        # Simple headings
        headers = ['AC Number', 'Gender', 'Name', 'Mobile', 'Membership Date', 'Paid Upto', 'Monthly Amount', 'Dues']

        # Write headings
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Get the data
        partners = self.env['res.partner'].sudo().search([])
        row = 1
        months = self._months_between()

        g_map = {'male': 'M', 'female': 'F', 'other': 'O'}

        for partner in partners:
            worksheet.write(row, 0, partner.ac_numnber_qa or '')
            worksheet.write(row, 1, g_map.get(partner.gender_qa, ''))
            worksheet.write(row, 2, partner.name or '')
            worksheet.write(row, 3, partner.mobile or '')
            worksheet.write(row, 4, str(partner.mem_date) if partner.mem_date else '')
            worksheet.write(row, 5, str(partner.trans_date_qa) if partner.trans_date_qa else '')
            worksheet.write(row, 6, partner.mlcontb or 0)
            worksheet.write(row, 7, (partner.mlcontb or 0) * months)
            row += 1

        workbook.close()
        output.seek(0)
        excel_file = output.read()
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': f'Monthly_Due_Report_{self.date_from}_{self.date_to}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_file),
            'store_fname': f'Monthly_Due_Report_{self.date_from}_{self.date_to}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

