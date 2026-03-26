# -*- coding: utf-8 -*-
from email.policy import default
from odoo.exceptions import ValidationError
from odoo import api, fields, models


class RequisitionProducts(models.Model):
    _name = 'requisition.order'
    _description = 'Requisition order'

    requisition_product_id = fields.Many2one(
        comodel_name='employee.purchase.requisition',
        help='Requisition product.')
    company_id = fields.Many2one(comodel_name='res.company' , related='requisition_product_id.company_id' , store=True)
    state = fields.Selection(
        string='State',
        related='requisition_product_id.state')
    requisition_type = fields.Selection(
        string='Requisition Type',
        selection=[
            ('purchase_order', 'Purchase Order'),
            # ('internal_transfer', 'Internal Transfer'),
        ],
        help='Type of requisition', required=True, default='purchase_order')
    product_id = fields.Many2one(
        comodel_name='product.product', required=True,
        help='Product')
    description = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False,
        precompute=True, help='Product description')
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure', 
                            required=True, readonly=False, help='Product quantity', default=1)
    
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=False, store=True)
    uom = fields.Char(
        related='product_id.uom_id.name',
        string='Unit of Measure', help='Product unit of measure')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Vendor', domain=[('supplier_rank', '>=', 1)],
        help='Vendor for the requisition',readonly=False)

    @api.onchange('product_id')
    def _onchange_product_uom(self):
        for rec in self:
            if rec.product_id:
                rec.product_uom = rec.product_id.uom_id.id

    @api.depends('product_id')
    def _compute_name(self):
        """Compute product description"""
        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.requisition_product_id.employee_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()

    @api.onchange('requisition_type')
    def _onchange_product(self):
        """Fetching product vendors"""
        vendors_list = [data.partner_id.id for data in
                        self.product_id.seller_ids]
        return {'domain': {'partner_id': [('id', 'in', vendors_list)]}}
