# -*- coding: utf-8 -*-
from odoo import api, fields, models
from collections import defaultdict
from odoo.exceptions import ValidationError, UserError , AccessError


class PurchaseRequisition(models.Model):
    """Class for adding fields and functions for purchase requisition model."""
    _name = 'employee.purchase.requisition'
    _description = 'Employee Purchase Requisition'
    _inherit = "mail.thread", "mail.activity.mixin"
    _order = 'id DESC'


    project_tag_ids = fields.Many2many('po.project.tags' , string="Project Tags")
    priority = fields.Selection([
        ('regular', 'Regular'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical')
    ], string='Priority', default='regular', required=True)
    material_req = fields.Char(string="Material Requisition")
    name = fields.Char(
        string="Reference No", readonly=True)
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee',
        required=True, help='Select an employee')
    dept_id = fields.Many2one(
        comodel_name='hr.department', string='Department',
        related='employee_id.department_id', store=True,
        help='Select an department')
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        required=True,
        default=lambda self: self.env.uid,
        domain=lambda self: [('share', '=', False), ('id', '!=', self.env.uid)],
        help='Select a user who is responsible for requisition')
    requisition_date = fields.Date(
        string="Requisition Date",
        default=lambda self: fields.Date.today(),
        help='Date of requisition')
    receive_date = fields.Date(
        string="Received Date", readonly=True, copy=False,
        help='Received date')
    requisition_deadline = fields.Date(
        string="Delivery Deadline",
        help="End date of purchase requisition")
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        default=lambda self: self.env.company,
        help='Select a company')
    requisition_order_ids = fields.One2many(
        comodel_name='requisition.order',
        inverse_name='requisition_product_id',
        required=True)
    confirm_id = fields.Many2one(
        comodel_name='res.users',
        string='Confirmed By', copy=False,
        default=lambda self: self.env.uid,
        readonly=True,
        help='User who confirmed the requisition.')
    manager_id = fields.Many2one(
        comodel_name='res.users', copy=False,
        string='Department Manager',
        readonly=True, help='Select a department manager')
    requisition_head_id = fields.Many2one(
        comodel_name='res.users', copy=False,
        string='Approved By',
        readonly=True,
        help='User who approved the requisition.')
    rejected_user_id = fields.Many2one(
        comodel_name='res.users', copy=False,
        string='Rejected By',
        readonly=True,
        help='User who rejected the requisition')
    confirmed_date = fields.Date(
        string='Confirmed Date', readonly=True, copy=False,
        help='Date of requisition confirmation')
    department_approval_date = fields.Date(
        string='Department Approval Date', copy=False,
        readonly=True,
        help='Department approval date')
    approval_date = fields.Date(
        string='Approved Date', readonly=True, copy=False,
        help='Requisition approval date')
    reject_date = fields.Date(
        string='Rejection Date', readonly=True, copy=False,
        help='Requisition rejected date')
    source_location_id = fields.Many2one(
        comodel_name='stock.location', copy=False,
        string='Source Location',
        help='Source location of requisition.')
    destination_location_id = fields.Many2one(
        comodel_name='stock.location', copy=False,
        string="Destination Location",
        help='Destination location of requisition.')
    delivery_type_id = fields.Many2one(
        comodel_name='stock.picking.type', copy=False,
        string='Delivery To',
        help='Type of delivery.')
    internal_picking_id = fields.Many2one(
        comodel_name='stock.picking.type', copy=False,
        string="Internal Picking")
    requisition_description = fields.Text(
        string="Reason For Requisition")
    purchase_count = fields.Integer(
        string='Purchase Count',
        help='Purchase count', copy=False,
        compute='_compute_purchase_count')
    internal_transfer_count = fields.Integer(
        string='Internal Transfer count',
        help='Internal transfer count', copy=False,
        compute='_compute_internal_transfer_count')
    state = fields.Selection(
        [('new', 'New'),
         ('waiting_department_approval', 'Waiting HOD Approval'),
         ('waiting_head_approval', 'Waiting Manager Approval'),
         ('approved', 'Approved'),
         ('purchase_order_created', 'Purchase Order Created'),
         ('received', 'Received'),
         ('cancelled', 'Cancelled')],
        default='new', copy=False, tracking=True)

    @api.model_create_multi
    def create(self, list_vals):
        """Function to generate purchase requisition sequence"""
        for vals in list_vals:
            # if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'employee.purchase.requisition') or 'New'
        result = super(PurchaseRequisition, self).create(list_vals)
        return result

    def write(self, vals):
        res = super(PurchaseRequisition, self).write(vals)
        state = vals.get('state')
        if state:
            if state not in ['new', 'cancelled', 'received']:
                for rec in self:
                    for line in rec.requisition_order_ids:
                        if line.requisition_type == 'purchase_order' and not line.partner_id:
                            raise ValidationError("Please select a vendor for all purchase order lines before proceeding.")
        return res

    def unlink(self):
        if not self.env.user.has_group('visio_tti_so_customize.group_delete_pr'):
            raise AccessError(_("You are not allowed to delete PRs."))

        return super(PurchaseRequisition, self).unlink()

    def action_reset_to_draft_requisition(self):
        self.ensure_one()
        self.write({'state': 'new'})


    def action_confirm_requisition(self):
        """Function to confirm purchase requisition"""
        # self.source_location_id = (
        #     self.employee_id.department_id.department_location_id.id) if (
        #     self.employee_id.department_id.department_location_id) else (
        #     self.env.ref('stock.stock_location_stock').id)
        # self.destination_location_id = (
        #     self.employee_id.employee_location_id.id) if (
        #     self.employee_id.employee_location_id) else (
        #     self.env.ref('stock.stock_location_stock').id)
        # self.delivery_type_id = (
        #     self.source_location_id.warehouse_id.in_type_id.id)
        # self.internal_picking_id = (
        #     self.source_location_id.warehouse_id.int_type_id.id)
        self.write({'state': 'waiting_department_approval'})
        self.confirm_id = self.env.uid
        self.confirmed_date = fields.Date.today()

    def action_cancel_requisition(self):
        """Function to cancel purchase requisition"""
        self.write({'state': 'cancelled'})

    def action_department_approval(self):
        """Approval from department"""
        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'purchase_order' and not rec.partner_id:
                raise ValidationError('Select a vendor')
        self.write({'state': 'waiting_head_approval'})
        self.manager_id = self.env.uid
        self.department_approval_date = fields.Date.today()

    def action_department_cancel(self):
        """Cancellation from department """
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_head_approval(self):
        """Approval from department head"""
        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'purchase_order' and not rec.partner_id:
                raise ValidationError('Select a vendor')
        self.write({'state': 'approved'})
        self.requisition_head_id = self.env.uid
        self.approval_date = fields.Date.today()

    def action_head_cancel(self):
        """Cancellation from department head"""
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_create_purchase_order(self):
        """Create partner-wise purchase orders with summed product quantities"""

        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'purchase_order' and not rec.partner_id:
                raise ValidationError('Select a vendor')

        partner_product_qty = defaultdict(lambda: defaultdict(lambda: {'qty': 0.0, 'uom': False}))

        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'purchase_order':
                partner_id = rec.partner_id.id
                product_id = rec.product_id.id
                data = partner_product_qty[partner_id][product_id]
                data['qty'] += rec.quantity
                data['uom'] = rec.product_uom.id

        for partner_id, products in partner_product_qty.items():
            order_lines = []
            for product_id, data in products.items():
                product = self.env['product.product'].browse(product_id)
                order_lines.append((0, 0, {
                    'product_id': product_id,
                    'product_qty': data['qty'],
                    'product_uom': data['uom'],
                    'price_unit': product.standard_price,
                }))

            self.env['purchase.order'].create({
                'partner_id': partner_id,
                'requisition_order': self.name,
                'order_line': order_lines,
                'project_tags': [(6, 0, self.project_tag_ids.ids)],
            })

        # for rec in self.requisition_order_ids:
        #     if rec.requisition_type == 'internal_transfer':
        #         self.env['stock.picking'].create({
        #             'location_id': self.source_location_id.id,
        #             'location_dest_id': self.destination_location_id.id,
        #             'picking_type_id': self.internal_picking_id.id,
        #             'requisition_order': self.name,
        #             'move_ids_without_package': [(0, 0, {
        #                 'name': rec.product_id.name,
        #                 'product_id': rec.product_id.id,
        #                 'product_uom': rec.product_id.uom_id.id,
        #                 'product_uom_qty': rec.quantity,
        #                 'location_id': self.source_location_id.id,
        #                 'location_dest_id': self.destination_location_id.id,
        #             })]
        #         })
        #     else:
        #         purchase_order = self.env['purchase.order'].create({
        #             'partner_id': rec.partner_id.id,
        #             'requisition_order': self.name,
        #             "order_line": [(0, 0, {
        #                 'product_id': rec.product_id.id,
        #                 'product_qty': rec.quantity,
        #             })]})
        #         # purchase_order.button_confirm()
        #         # if purchase_order.state == 'purchase':
        #         #     purchase_order.button_done()

        self.write({'state': 'purchase_order_created'})

    def _compute_internal_transfer_count(self):
        """Function to compute the transfer count"""
        self.internal_transfer_count = self.env['stock.picking'].search_count([
            ('requisition_order', '=', self.name)])

    def _compute_purchase_count(self):
        """Function to compute the purchase count"""
        self.purchase_count = self.env['purchase.order'].search_count([
            ('requisition_order', '=', self.name)])

    def action_receive(self):
        """Received purchase requisition"""
        self.write({'state': 'received'})
        self.receive_date = fields.Date.today()

    def get_purchase_order(self):
        """Purchase order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_order', '=', self.name)],
        }

    def get_internal_transfer(self):
        """Internal transfer smart tab view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfers',
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_order', '=', self.name)],
        }

