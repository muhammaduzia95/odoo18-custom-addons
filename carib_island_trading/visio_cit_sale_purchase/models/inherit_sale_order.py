# D:\Visiomate\Odoo\odoo18\custom_addons\carib_island_trading\visio_cit_sale_purchase\models\inherit_sale_order.py
from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    driver_so = fields.Char(string="Driver", tracking=True)
    third_party_logistics_so = fields.Char(string="3PL", tracking=True)

    logistics_stage = fields.Selection([
        ('in_transit', "In Transit"),
        ('delivered_vendor_port', "Delivered to Vendor’s Local Port"),
        ('delivered_customer_port', "Delivered to Customer’s Destination Port"),
        ('importing_clearance', "Importing / Customs Clearance"),
        ('book_container', "Book Container"),
        ('booking_confirmed', "Booking Confirmed"),
        ('ready_dispatch', "Ready for Dispatch"),
        ('on_hold', "On Hold"),
        ('cancelled', "Cancelled"),
        ('in_progress', "In Progress"),
        ('delivered_customer_ff', "Delivered to Customer Freight Forwarder"),
        ('delivered_customer_warehouse', "Delivered to Customer Warehouse"),
        ('cleanup_3pl', "Cleanup at 3PL"),
        ('separation_3pl', "Separation at 3PL"),
        ('counting_3pl', "Counting at 3PL"),
        ('customer_picked_up', "Customer Picked Up"),
    ], string="Logistics Stage", tracking=True)

    state = fields.Selection([
        ('draft', "Request Deposit"),
        ('request_balance', "Request Balance Payment"),
        ('sent', "Share Invoice"),
        ('sale', "Request Order Confirmation"),
        ('share_logistic_docs', "Share Logistic Documents"),
        ('request_payment_receipt', "Request Payment Receipt"),
        ('check_payment_received', "Check if Payment Was Received"),
        ('share_credit_note', "Share Credit Note"),
        ('cancel', "Investigate Missing / Damaged Goods"),
    ], string="Status", readonly=False, copy=False, index=True, tracking=3, default='draft')

    STATE_SEQUENCE = [
        'draft',
        'request_balance',
        'sent',
        'sale',
        'share_logistic_docs',
        'request_payment_receipt',
        'check_payment_received',
        'share_credit_note',
        'cancel',
    ]

    # Button of stage
    def action_next_stage_so(self):
        for order in self:
            seq = self.STATE_SEQUENCE
            if order.state in seq:
                idx = seq.index(order.state)
                if idx < len(seq) - 1:
                    order.state = seq[idx + 1]

    # Button of stage
    def action_previous_stage_so(self):
        for order in self:
            seq = self.STATE_SEQUENCE
            if order.state in seq:
                idx = seq.index(order.state)
                if idx > 0:
                    order.state = seq[idx - 1]

    logistics_company_so_col = fields.Many2one("sub.shipping", string="Logistics Company")
    so_logistics_company_col = fields.Many2one("shipping.methods", string="Logistics Company")
    notes_cit_so_col = fields.Char(string="Notes")
    packing_request_so_col = fields.Char(string="Packing Request")
    pickup_address_so_col = fields.Char(string="Pickup Address")
    delivery_address_so_col = fields.Char(string="Delivery Address")
    incoterms_cit_so_col = fields.Char(string="Incoterms")
    weight_cit_so_col = fields.Char(string="Weight")
    booking_number_cit_so_col = fields.Char(string="Booking Number")
    bol_status_so_col = fields.Boolean(string="BOL Status")
    shipment_status_so_col = fields.Char(string="Shipment Status")
    charge_to_customer_so_col = fields.Float(string="Charge to Customer")
    driver_so_col = fields.Char(string="Driver", tracking=True)
    third_party_logistics_so_col = fields.Float(string="3PL", tracking=True)

    # Adding the product line of shipping in sale order lines
    def _ensure_logistics_details_line_col2(self):
        for order in self:
            if not order.so_logistics_company_col:
                raise UserError(_("Please select a Logistics Company first."))

            product = self.env['product.product'].search(
                [('name', '=', order.so_logistics_company_col.name)], limit=1
            )
            if not product:
                raise UserError(
                    _("No product found with name '%s' (needed for logistics line).")
                    % order.so_logistics_company_col.name
                )

            so_line = order.order_line.filtered(lambda l: l.product_id == product)[:1]
            if so_line:
                so_line.price_unit = order.charge_to_customer_so_col
            else:
                order.order_line.create({
                    'order_id': order.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': 1,
                    'product_uom': product.uom_id.id,
                    'price_unit': order.charge_to_customer_so_col or 0.0,
                })

    # Button Add Line action
    def action_accept_logistics_details_col2(self):
        print("action_accept_logistics_details_col2 Triggered")
        for order in self:
            if not order.charge_to_customer_so_col or order.charge_to_customer_so_col <= 0:
                raise ValidationError(_("Charge to Customer (Col 2) should be greater than 0"))

            order._ensure_logistics_details_line_col2()
            order.logistics_details_accepted = True
        return True

    truck_type_so = fields.Char(string="Truck Type")

    pickup_contact_name_so = fields.Char(string="Pickup Contact Name")
    pickup_contact_number_so = fields.Char(string="Pickup Contact Number")
    pickup_email_so = fields.Char(string="Pickup Email")
    pickup_time_scheduled_so = fields.Datetime(string="Pickup Time Scheduled")
    pickup_notes_so = fields.Text(string="Pickup Notes")

    total_cartons_so = fields.Integer(string="Total Cartons")
    total_palettes_so = fields.Integer(string="Total Palettes")
    goods_description_so = fields.Text(string="Description of Goods")
    delivery_notes_so = fields.Text(string="Delivery Notes")





    delivery_doc_upload_so = fields.Many2many(
        'ir.attachment',
        'so_damaged_photos_rel',
        'so_id',
        'attachment_id'
    )

    additional_notes_so = fields.Text(string="Additional Notes")
    billed_to_customer_so = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Billed to Customer?")

    delivery_receipt_signed_pod_so = fields.Boolean(string="Delivery Receipt Signed POD (SO)") #this field is not in use

