
import base64
import io

from PyPDF2 import PdfFileWriter, PdfFileReader
from PyPDF2.generic import NameObject, createStringObject
import pdfkit

from odoo import models, fields, api
from odoo.tools import format_amount, format_date, format_datetime, pdf


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _get_form_fields_mapping(self, order, doc_line_id_mapping=None):
        res = super()._get_form_fields_mapping(order, doc_line_id_mapping)
        res['partner_name_left']: order.partner_id.name
        res['partner_name_center']: order.partner_id.name
        res['partner_id__name_left']: order.partner_id.name
        res['partner_id__name_center']: order.partner_id.name

        res['opportunity_id__name'] = order.opportunity_id.name
        res['opportunity_id__name_left'] = order.opportunity_id.name
        res['opportunity_id__name_center'] = order.opportunity_id.name

        res['origin'] = order.origin
        res['origin_left'] = order.origin
        res['origin_center'] = order.origin

        res['date_order'] = order.date_order
        res['date_order_left'] = order.date_order
        res['date_order_center'] = order.date_order

        res['date_only'] = order.date_order.date()
        return res

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        result = super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)
        if self._get_report(report_ref).report_name != 'sale.report_saleorder':
            return result

        if self._get_report(report_ref).report_name == 'sale.report_saleorder':
            orders = self.env['sale.order'].browse(res_ids)

            for order in orders:
                content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf('sale_pdf_quote_builder.action_report_saleorder_raw', res_ids=order.ids)

                pdf_bytes = pdfkit.from_string(order.description or '', False)
                initial_stream = result[order.id]['stream']
                if initial_stream:
                    order_template = order.sale_order_template_id
                    header_record = order_template if order_template.sale_header else order.company_id
                    footer_record = order_template if order_template.sale_footer else order.company_id
                    has_header = bool(header_record.sale_header)
                    has_footer = bool(footer_record.sale_footer)
                    included_product_docs = self.env['product.document']
                    doc_line_id_mapping = {}
                    for line in order.order_line:
                        product_product_docs = line.product_id.product_document_ids
                        product_template_docs = line.product_template_id.product_document_ids
                        doc_to_include = (
                            product_product_docs.filtered(lambda d: d.attached_on == 'inside')
                            or product_template_docs.filtered(lambda d: d.attached_on == 'inside')
                        )
                        included_product_docs = included_product_docs | doc_to_include
                        doc_line_id_mapping.update({doc.id: line.id for doc in doc_to_include})

                    if (not has_header and not included_product_docs and not has_footer):
                        continue

                    writer = PdfFileWriter()
                    if has_header:
                        self._add_pages_to_writer(writer, base64.b64decode(header_record.sale_header))
                    if included_product_docs:
                        for doc in included_product_docs:
                            self._add_pages_to_writer(
                                writer, base64.b64decode(doc.datas), doc_line_id_mapping[doc.id]
                            )

                    if pdf_bytes and order.description != '':
                        self._add_pages_to_writer(writer, pdf_bytes)
                        self._add_pages_to_writer(writer, content)
                    else:
                        self._add_pages_to_writer(writer, initial_stream.getvalue())

                    if has_footer:
                        self._add_pages_to_writer(writer, base64.b64decode(footer_record.sale_footer))

                    form_fields = self._get_form_fields_mapping(order, doc_line_id_mapping)
                    pdf.fill_form_fields_pdf(writer, form_fields=form_fields)
                    with io.BytesIO() as _buffer:
                        writer.write(_buffer)
                        stream = io.BytesIO(_buffer.getvalue())
                    result[order.id].update({'stream': stream})

        return result