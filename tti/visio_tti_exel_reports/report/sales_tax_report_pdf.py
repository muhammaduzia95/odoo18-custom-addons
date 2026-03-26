# custom_addons\tti\visio_tti_exel_reports\report\sales_tax_report_pdf.py
# -*- coding: utf-8 -*-
from odoo import models, fields


class SalesTaxReportQweb(models.AbstractModel):
    _name = 'report.visio_tti_exel_reports.report_sales_tax_pdf_template'
    _description = 'Sales Tax Report (QWeb)'

    def _get_report_values(self, docids, data=None):
        docs = self.env['sales.tax.report.wizard'].browse(docids)
        wizard = docs[:1]  # single wizard or empty
        if not wizard:
            return {
                'doc_ids': [],
                'doc_model': 'sales.tax.report.wizard',
                'docs': docs,
                'from_date_str': '',
                'to_date_str': '',
                'lines': [],
                'totals': {'untaxed': 0.0, 'tax': 0.0, 'total': 0.0},
            }

        date_from, date_to = wizard.date_from, wizard.date_to
        Move = self.env['account.move'].sudo()

        # Build domain with optional state filter
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]
        if wizard.state_id:
            domain += [
                '|',
                ('partner_id.state_id', '=', wizard.state_id.id),
                ('partner_id.commercial_partner_id.state_id', '=', wizard.state_id.id),
            ]

        invoices = Move.search(domain, order='invoice_date asc, name asc')

        pkr = self.env.ref('base.PKR', raise_if_not_found=False) or wizard.company_id.currency_id

        lines = []
        tot_untaxed = tot_tax = tot_total = 0.0
        sr = 1

        for inv in invoices:
            partner = inv.partner_id
            conv_date = inv.invoice_date or fields.Date.context_today(self)
            if inv.currency_id and inv.currency_id != pkr:
                untaxed = inv.currency_id._convert(inv.amount_untaxed, pkr, inv.company_id, conv_date)
                tax = inv.currency_id._convert(inv.amount_tax, pkr, inv.company_id, conv_date)
                total = inv.currency_id._convert(inv.amount_total, pkr, inv.company_id, conv_date)
                rate = inv.currency_id._convert(1.0, pkr, inv.company_id, conv_date)
            else:
                untaxed = inv.amount_untaxed
                tax = inv.amount_tax
                total = inv.amount_total
                rate = 1.0

            # Optional partner extras (safe guards for custom fields)
            strn = getattr(partner, 'strn', '') or ''
            if partner and 'sales_taxes' in partner._fields and partner.sales_taxes:
                tax_names = ', '.join(partner.sales_taxes.mapped('name'))
            else:
                tax_names = ''

            lines.append({
                'sr': sr,
                'manufacturer': partner.name or '',
                'ntn': partner.vat or '',
                'strn': strn,
                'invoice_no': inv.name or '',
                'invoice_date': inv.invoice_date,
                'untaxed_pkr': untaxed,
                'tax_pkr': tax,
                'total_pkr': total,
                'exchange_rate': rate,
                'currency': inv.currency_id.name or '',
                'state': (partner.state_id.name if partner and partner.state_id else ''),
                'tax_rate': tax_names,
            })

            tot_untaxed += untaxed or 0.0
            tot_tax += tax or 0.0
            tot_total += total or 0.0
            sr += 1

        # Dynamic report title only — DO NOT hide any columns
        tax_rate_label = 'Sales Tax Report'
        if wizard.state_id:
            base_state = (wizard.state_id.display_name or wizard.state_id.name or '')
            base_state = base_state.split(' (')[0].strip().lower()

            label_map = {
                'punjab': 'Punjab Sales Tax Report',
                'sindh': 'Sindh Sales Tax Report',
                'kpk': 'KPK Sales Tax Report',
                'khyber pakhtunkhwa': 'KPK Sales Tax Report',
                'international': 'International Sales Tax Report',
            }
            tax_rate_label = label_map.get(base_state, 'Sales Tax Report')
            print("tax_rate_label", tax_rate_label)

        # No column hiding; totals tail is always 4 cells
        right_colspan = 4

        return {
            'doc_ids': docs.ids,
            'doc_model': 'sales.tax.report.wizard',
            'docs': docs,
            'from_date_str': date_from.strftime('%d/%m/%Y') if date_from else '',
            'to_date_str': date_to.strftime('%d/%m/%Y') if date_to else '',
            'lines': lines,
            'totals': {
                'untaxed': tot_untaxed,
                'tax': tot_tax,
                'total': tot_total,
            },
            'company': self.env.company,
            'res_company': self.env.company,
            'tax_rate_label': tax_rate_label,
            'right_colspan': right_colspan,
        }
