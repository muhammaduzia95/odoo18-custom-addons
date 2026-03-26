# quran_academy/visio_contact_extension_qa/wizard/elections_wizard.py
from odoo import models, fields, api
import base64
import io
import xlsxwriter


class ElectionsWizard(models.TransientModel):
    _name = 'elections.wizard'
    _description = 'Elections – filters & dates'

    # fields shown in the form
    member_selection = fields.Selection(
        [('def', 'Default'), ('moh', 'Mohsinin'), ('per', 'Permanent'), ('gen', 'General')],
        string='Member Type',
        required=True,
        default='moh'
    )

    trans_upto_date = fields.Date(string='Trans Upto')
    mem_date_voters = fields.Date(string='Member Date (Voters)')
    mem_date_candidate = fields.Date(string='Member Date (Candidate)')

    report_type = fields.Selection(
        [('pdf', 'PDF'), ('excel', 'Excel')],
        string="Report Type",
        required=True,
        default='pdf'
    )

    def get_member_type_display(self):
        return dict(self._fields['member_selection'].selection).get(self.member_selection, '')

    # candidates

    def _get_candidate_lines(self):
        """
        Return the res.partner records that are allowed
        to stand for the election.

        Rules
        -----
        • Contact type  = the member type chosen in the wizard
        • Gender        = male  (gender_qa == 'male')
        • Transaction   = trans_date_qa ≤ “Trans Up to”  (if filled)
        • Mem. date     = mem_date      ≤ “Mem Date Candidate” (if filled)
        """
        self.ensure_one()

        # map the wizard’s codes to the values stored on res.partner
        type_map = {
            'def': 'default',
            'moh': 'mohsinin',
            'per': 'permanent',
            'gen': 'general',
        }

        domain = [
            ('show_records_qa', '=', type_map[self.member_selection]),
            ('gender_qa', '=', 'male'),  # ← male-only rule
        ]

        if self.trans_upto_date:
            domain += [
                ('trans_date_qa', '!=', False),
                ('trans_date_qa', '<=', self.trans_upto_date)
            ]

        if self.mem_date_candidate:
            domain.append(('mem_date', '<=', self.mem_date_candidate))

        return self.env['res.partner'].sudo().search(domain, order='acno_qa')

    def action_list_candidates(self):
        self.ensure_one()
        if self.report_type == 'pdf':
            return self.env.ref(
                'visio_contact_extension_qa.action_election_candidates_report'
            ).report_action(self, data={})
        else:
            return self._export_candidates_excel()

    def action_label_candidates(self):
        self.ensure_one()
        return self.env.ref(
            'visio_contact_extension_qa.action_election_candidate_labels_report'
        ).report_action(self, data={})

    # voters

    def _get_voter_lines(self):
        """
        Return the res.partner records that MAY VOTE.

        Rules
        -----
        • Contact type  = wizard.member_selection
        • Gender        = any (male OR female)
        • Transaction   = trans_date_qa ≤ “Trans Up to”          (if set)
        • Mem. date     = mem_date      ≤ “Mem Date Voters”      (if set)
        """
        self.ensure_one()

        type_map = {
            'def': 'default',
            'moh': 'mohsinin',
            'per': 'permanent',
            'gen': 'general',
        }

        domain = [
            ('show_records_qa', '=', type_map[self.member_selection]),
        ]

        if self.trans_upto_date:
            domain += [
                ('trans_date_qa', '!=', False),  # ignore empty dates
                ('trans_date_qa', '<=', self.trans_upto_date),
            ]
        if self.mem_date_voters:
            domain += [
                ('mem_date', '!=', False),
                ('mem_date', '<=', self.mem_date_voters),
            ]

        return self.env['res.partner'].sudo().search(domain, order='acno_qa')

    def action_list_voters(self):
        self.ensure_one()
        if self.report_type == 'pdf':
            return self.env.ref(
                'visio_contact_extension_qa.action_election_voters_report'
            ).report_action(self, data={})
        else:
            return self._export_voters_excel()

    def action_label_voters(self):
        self.ensure_one()
        return self.env.ref(
            'visio_contact_extension_qa.action_election_voter_labels_report'
        ).report_action(self, data={})

    # excel code

    def _export_candidates_excel(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Candidates List')

        headers = ['ACNO', 'F Name', 'Address', 'Tel', 'Phone', 'Cont', 'Mem Date', 'Trans Date']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        candidates = self._get_candidate_lines()
        row = 1
        for p in candidates:
            worksheet.write(row, 0, p.acno_qa or '')
            worksheet.write(row, 1, p.name or '')
            address = ', '.join(filter(None, [p.street or '', p.street2 or '', p.street3_qa or '']))
            worksheet.write(row, 2, address)
            worksheet.write(row, 3, p.phone or '')
            worksheet.write(row, 4, p.mobile or '')
            worksheet.write(row, 5, p.country_id.code or '')
            worksheet.write(row, 6, str(p.mem_date) if p.mem_date else '')
            worksheet.write(row, 7, str(p.trans_date_qa) if p.trans_date_qa else '')
            row += 1

        workbook.close()
        output.seek(0)
        excel_file = output.read()
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': f'Candidates_List_{self.id}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_file),
            'store_fname': f'Candidates_List_{self.id}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _export_voters_excel(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Voters List')

        headers = ['ACNO', 'F Name', 'Address 1', 'Address 2', 'Address 3', 'Mem Date', 'Trans Date', 'Sex']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        voters = self._get_voter_lines()
        row = 1
        for p in voters:
            worksheet.write(row, 0, p.acno_qa or '')
            worksheet.write(row, 1, p.name or '')
            worksheet.write(row, 2, p.street or '')
            worksheet.write(row, 3, p.street2 or '')
            worksheet.write(row, 4, p.street3_qa or '')
            worksheet.write(row, 5, str(p.mem_date) if p.mem_date else '')
            worksheet.write(row, 6, str(p.trans_date_qa) if p.trans_date_qa else '')
            worksheet.write(row, 7, (p.gender_qa[0].upper() if p.gender_qa else ''))
            row += 1

        workbook.close()
        output.seek(0)
        excel_file = output.read()
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': f'Voters_List_{self.id}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_file),
            'store_fname': f'Voters_List_{self.id}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
