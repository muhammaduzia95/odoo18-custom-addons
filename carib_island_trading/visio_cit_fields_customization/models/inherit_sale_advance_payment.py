# carib_island_trading\visio_cit_fields_customization\models\inherit_sale_advance_payment.py
from odoo import models, fields, _
from odoo.tools import format_date


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    advance_payment_method = fields.Selection(
        selection=[
            ('delivered', "Regular invoice"),
            ('percentage', "Deposit payment (percentage)"),
            ('fixed', "Deposit payment (fixed amount)"),
        ],
        string="Create Invoice",
        default='delivered',
        required=True,
        help="A standard invoice is issued with all the order lines ready for invoicing, "
             "according to their invoicing policy (based on ordered or delivered quantity)."
    )

    amount = fields.Float(
        string="Deposit Payment",
        help="The percentage or fixed amount to be invoiced in advance."
    )

    def _get_down_payment_description(self, order):
        """Return the text that will become the invoice line’s description."""
        self.ensure_one()
        if self.advance_payment_method == 'percentage':
            return _("Deposit payment of %s%%", self.amount)
        return _("Deposit Payment")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_downpayment_description(self):
        """
        Override to rename 'Down Payment' → 'Deposit Payment' in all display cases:
        - Section line
        - Draft
        - Cancelled
        - Valid invoice with reference and date
        """
        self.ensure_one()

        if self.display_type:
            return _("Deposit Payments")

        dp_state = self._get_downpayment_state()
        name = _("Deposit Payment")

        if dp_state == 'draft':
            name = _(
                "Deposit Payment: %(date)s (Draft)",
                date=format_date(self.env, self.create_date.date()),
            )
        elif dp_state == 'cancel':
            name = _("Deposit Payment (Cancelled)")
        else:
            invoice = self._get_invoice_lines().filtered(
                lambda aml: aml.quantity >= 0
            ).move_id.filtered(lambda move: move.move_type == 'out_invoice')
            if len(invoice) == 1 and invoice.payment_reference and invoice.invoice_date:
                name = _(
                    "Deposit Payment (ref: %(reference)s on %(date)s)",
                    reference=invoice.payment_reference,
                    date=format_date(self.env, invoice.invoice_date),
                )

        return name
