# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\inherit_account_move.py
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    customer_po_no = fields.Char(string="Customer P.O. No.")
    customer_po_date = fields.Date(string="Customer P.O. Date")
