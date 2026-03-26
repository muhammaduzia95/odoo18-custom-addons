# D:\Visiomate\Odoo\odoo18\custom_addons\carib_island_trading\visio_cit_sale_purchase\models\inherit_purchase_order.py
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    driver = fields.Char(string="Driver", tracking=True)
    third_party_logistics = fields.Char(string="3PL", tracking=True)
    state = fields.Selection([
        ('sent', 'Vendor Accepted Order'),
        ('cancel', 'Order Cancelled'),
        ('draft', 'Under Processing'),
        ('to approve', 'Needs Work'),
        ('purchase', 'Investigate Missing/Damaged Goods'),
        ('done', 'Order Completed'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    logistics_stage_po = fields.Selection([
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

    STATE_SEQUENCE = [
        'sent',
        'cancel',
        'draft',
        'to approve',
        'purchase',
        'done',
    ]

    # # --- Navigation buttons ---
    # def action_next_stage_po(self):
    #     """Move to the next state."""
    #     for order in self:
    #         seq = self.STATE_SEQUENCE
    #         if order.state in seq:
    #             idx = seq.index(order.state)
    #             if idx < len(seq) - 1:
    #                 order.state = seq[idx + 1]
    #
    # def action_previous_stage_po(self):
    #     """Move to the previous state."""
    #     for order in self:
    #         seq = self.STATE_SEQUENCE
    #         if order.state in seq:
    #             idx = seq.index(order.state)
    #             if idx > 0:
    #                 order.state = seq[idx - 1]

    def action_next_stage_po(self):
        """Move to the next state."""
        for order in self:
            seq = self.STATE_SEQUENCE
            _logger.info(
                "[PO NEXT] PO(%s) current_state=%s sequence=%s",
                order.id, order.state, seq
            )
            if order.state not in seq:
                _logger.warning(
                    "[PO NEXT] PO(%s) state '%s' NOT in STATE_SEQUENCE",
                    order.id, order.state
                )
                continue
            idx = seq.index(order.state)
            if idx < len(seq) - 1:
                next_state = seq[idx + 1]
                _logger.info(
                    "[PO NEXT] PO(%s) moving %s → %s",
                    order.id, order.state, next_state
                )
                order.state = next_state
            else:
                _logger.info(
                    "[PO NEXT] PO(%s) already at LAST state (%s)",
                    order.id, order.state
                )

    def action_previous_stage_po(self):
        """Move to the previous state."""
        for order in self:
            seq = self.STATE_SEQUENCE

            _logger.info(
                "[PO PREV] PO(%s) current_state=%s sequence=%s",
                order.id, order.state, seq
            )

            if order.state not in seq:
                _logger.warning(
                    "[PO PREV] PO(%s) state '%s' NOT in STATE_SEQUENCE",
                    order.id, order.state
                )
                continue

            idx = seq.index(order.state)

            if idx > 0:
                prev_state = seq[idx - 1]
                _logger.info(
                    "[PO PREV] PO(%s) moving %s → %s",
                    order.id, order.state, prev_state
                )
                order.state = prev_state
            else:
                _logger.info(
                    "[PO PREV] PO(%s) already at FIRST state (%s)",
                    order.id, order.state
                )

    # Purchase Col 2 (Logistic Details Notebook)
    logistics_company_col = fields.Many2one(
        "sub.shipping",
        string="Logistics Company",
        # compute="_compute_logistics_company_col",
        store=True,
    )

    logistics_company_main_col = fields.Many2one(
        "shipping.methods",
        string="Logistics Company",
        compute="_compute_logistics_company_main_col",
        store=True,
        readonly=True,
    )

    packing_request_col = fields.Char(string="Packing Request")
    notes_cit_col = fields.Char(string="Notes")
    pickup_address_col = fields.Char(string="Pickup Address")
    delivery_address_col = fields.Char(string="Delivery Address")
    incoterms_cit_col = fields.Char(string="Incoterms")
    weight_cit_col = fields.Char(string="Weight")
    booking_number_cit_col = fields.Char(string="Booking Number")
    bol_status_col = fields.Boolean(string="BOL Status")
    shipment_status_col = fields.Char(string="Shipment Status")
    charge_to_customer_col = fields.Float(
        string="Charge to Customer",
        compute="_compute_charge_to_customer_col",
        store=True,
        readonly=True,
    )
    driver_col = fields.Char(string="Driver Assigned", tracking=True)
    third_party_logistics_col = fields.Float(string="3PL", tracking=True)

    @api.depends('logistics_company_col', 'logistics_ids')
    def _compute_logistics_company_main_col(self):
        for po in self:
            debug_hdr = f"[DEBUG][compute_main_col] PO({po.id})"

            line = po.logistics_ids[1] if len(po.logistics_ids) > 1 else False

            if line and line.shipping_method_id:
                print(
                    f"{debug_hdr} -> 2nd line {line.id} shipping_method={line.shipping_method_id.id}"
                )
                po.logistics_company_main_col = line.shipping_method_id
            else:
                print(f"{debug_hdr} -> no 2nd line or missing shipping_method_id")
                po.logistics_company_main_col = False

    @api.depends('logistics_company_col', 'logistics_ids.sub_shipping_id', 'logistics_ids.price')
    def _compute_charge_to_customer_col(self):
        for po in self:
            debug_hdr = f"[DEBUG][compute_charge_to_customer_col] PO({po.id})"

            if po.logistics_company_col:
                # Find the logistics line matching the SELECTED company
                line = po.logistics_ids.filtered(
                    lambda l: l.sub_shipping_id == po.logistics_company_col
                )[:1]

                if line:
                    print(f"{debug_hdr} Selected company={po.logistics_company_col.id} -> price={line.price}")
                    po.charge_to_customer_col = line.price
                else:
                    print(f"{debug_hdr} Selected company={po.logistics_company_col.id} -> no matching line")
                    po.charge_to_customer_col = 0.0  # up to you if reset or keep
            else:
                print(f"{debug_hdr} No logistics_company_col selected")
                po.charge_to_customer_col = 0.0  # or keep existing

    # function for getting the pickup/delivery address form the logistics lines
    @api.onchange('logistics_ids', 'logistics_company_id')
    def _onchange_fill_pickup_delivery(self):
        for po in self:
            debug_hdr = f"[DEBUG][pickup/delivery onchange] PO({po.id})"

            # If logistics lines are removed → clear addresses
            if not po.logistics_ids:
                print(f"{debug_hdr} all logistics lines removed → clearing fields")
                po.pickup_address = False
                po.delivery_address = False
                return

            # If user hasn't selected any logistics company → DO NOTHING
            if not po.logistics_company_id:
                print(f"{debug_hdr} no company selected → clearing fields & exit")
                po.pickup_address = False
                po.delivery_address = False
                return

            # User selected logistics_company_id → find matching line
            line = po.logistics_ids.filtered(
                lambda l: l.sub_shipping_id == po.logistics_company_id
            )[:1]

            if not line:
                # Selected company, but no matching line exists
                print(f"{debug_hdr} selected company but no matching line → clearing")
                po.pickup_address = False
                po.delivery_address = False
                return

            # Matching line found → update pickup & delivery
            print(f"{debug_hdr} using matching line {line.id}")

            po.pickup_address = line.pickup_address_port or False
            po.delivery_address = line.delivery_address_port or False

    # function for getting the pickup/delivery address form the logistics lines COL 2
    @api.onchange('logistics_ids', 'logistics_company_col')
    def _onchange_fill_pickup_delivery_col(self):
        for po in self:
            debug_hdr = f"[DEBUG][pickup/delivery COL] PO({po.id})"

            # If lines removed → clear fields
            if not po.logistics_ids:
                print(f"{debug_hdr} logistics removed → clearing")
                po.pickup_address_col = False
                po.delivery_address_col = False
                return

            # If no company selected → clear fields so user may enter manually
            if not po.logistics_company_col:
                print(f"{debug_hdr} NO company selected → clearing fields")
                po.pickup_address_col = False
                po.delivery_address_col = False
                return

            # Find matching line for selected company
            line = po.logistics_ids.filtered(
                lambda l: l.sub_shipping_id == po.logistics_company_col
            )[:1]

            if not line:
                print(f"{debug_hdr} no matching line for company={po.logistics_company_col.id}")
                po.pickup_address_col = False
                po.delivery_address_col = False
                return

            print(f"{debug_hdr} using line {line.id}")

            # Auto-fill COLUMN-2 values from matched line
            po.pickup_address_col = line.pickup_address_port or False
            po.delivery_address_col = line.delivery_address_port or False

    # Trucking Information
    # trucking_company_po = fields.Char(string="Trucking Company")
    # driver_assigned_po = fields.Char(string="Driver Assigned")
    truck_type_po = fields.Char(string="Truck Type")

    # Pickup Details
    # pickup_address_po = fields.Char(string="Pickup Address")
    pickup_contact_name_po = fields.Char(string="Pickup Contact Name")
    pickup_contact_number_po = fields.Char(string="Pickup Contact Number")
    pickup_email_po = fields.Char(string="Pickup Email")
    pickup_time_scheduled_po = fields.Datetime(string="Pickup Time Scheduled")
    pickup_notes_po = fields.Text(string="Pickup Notes")

    # Delivery Details
    # delivery_address_po = fields.Char(string="Delivery Address")

    total_cartons_po = fields.Integer(string="Total Cartons")
    total_palettes_po = fields.Integer(string="Total Palettes")
    # approx_weight_po = fields.Float(string="Approx Weight")
    goods_description_po = fields.Text(string="Description of Goods")
    delivery_notes_po = fields.Text(string="Delivery Notes")

    delivery_doc_upload = fields.Many2many(
        'ir.attachment',
        'po_damaged_photos_rel',
        'po_id',
        'attachment_id',
        string="Attachment"
    )

    additional_notes_po = fields.Text(string="Additional Notes")

    # Billing Information
    billed_to_customer_po = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No')
        ],
        string="Billed to Customer?"
    )


    # Syncing the fields from PO to SO
    def _sync_to_sale_order(self):
        """Extend sync to include Driver, 3PL and logistics fields."""
        # Call original sync method first
        super()._sync_to_sale_order()

        SaleOrder = self.env['sale.order']
        so_fields = SaleOrder._fields

        extra_field_map = {
            "driver": "driver_so",
            "third_party_logistics": "third_party_logistics_so",
            "logistics_stage_po": "logistics_stage",

            # col 2
            "logistics_company_col": "logistics_company_so_col",
            "logistics_company_main_col": "so_logistics_company_col",
            "packing_request_col": "packing_request_so_col",
            "notes_cit_col": "notes_cit_so_col",
            "pickup_address_col": "pickup_address_so_col",
            "delivery_address_col": "delivery_address_so_col",
            "incoterms_cit_col": "incoterms_cit_so_col",
            "weight_cit_col": "weight_cit_so_col",
            "booking_number_cit_col": "booking_number_cit_so_col",
            "bol_status_col": "bol_status_so_col",
            "shipment_status_col": "shipment_status_so_col",
            "charge_to_customer_col": "charge_to_customer_so_col",
            "driver_col": "driver_so_col",
            "third_party_logistics_col": "third_party_logistics_so_col",

            # Trucking
            "truck_type_po": "truck_type_so",

            # Pickup Details
            "pickup_contact_name_po": "pickup_contact_name_so",
            "pickup_contact_number_po": "pickup_contact_number_so",
            "pickup_email_po": "pickup_email_so",
            "pickup_time_scheduled_po": "pickup_time_scheduled_so",
            "pickup_notes_po": "pickup_notes_so",

            # Delivery Details
            "total_cartons_po": "total_cartons_so",
            "total_palettes_po": "total_palettes_so",
            "goods_description_po": "goods_description_so",
            "delivery_notes_po": "delivery_notes_so",

            # Delivery Documentation
            "delivery_doc_upload": "delivery_doc_upload_so",
            "additional_notes_po": "additional_notes_so",

            # Billing
            "billed_to_customer_po": "billed_to_customer_so",
        }

        for po in self:
            so = po._get_related_sale_order()
            if not so:
                continue

            vals = {}
            for po_f, so_f in extra_field_map.items():
                if so_f not in so_fields:
                    continue

                val = getattr(po, po_f)
                field_def = so_fields[so_f]

                if field_def.type == 'many2many':
                    vals[so_f] = [(6, 0, val.ids)]
                else:
                    vals[so_f] = val.id if hasattr(val, "id") else val

            if vals:
                # DEBUG (optional)
                # print(f"[SYNC PO→SO] PO {po.id} -> SO {so.id} VALS = {vals}")
                so.sudo().write(vals)

    freight_cost = fields.Float(string="Freight Cost",)
    delivery_cost = fields.Float(string="Delivery Cost",)
    delivery_charged = fields.Float(string="Delivery Charged",)
    tpl_cost = fields.Float(string="3PL Cost",)

    # if any of given logistics_stage_po is set then PO state becomes done i.e. 'Order Completed'
    # _AUTO_DONE_LOGISTICS = {'delivered_customer_ff', 'delivered_customer_warehouse', 'customer_picked_up'}
    #
    # @api.onchange('logistics_stage_po')
    # def _onchange_logistics_stage_po_set_done(self):
    #     for po in self:
    #         if po.logistics_stage_po in self._AUTO_DONE_LOGISTICS:
    #             po.state = 'Order Completed'


