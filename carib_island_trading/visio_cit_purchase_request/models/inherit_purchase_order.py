# \carib_island_trading\visio_cit_purchase_request\models\inherit_purchase_order.py
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    logistics_ids = fields.One2many('purchase.order.logistics', 'order_id', string="Logistics")

    # PO / Notebook / Page / Logistic Details fields
    logistics_company_id = fields.Many2one("sub.shipping", string="Logistics Company", )
    # logistics_company_main = fields.Many2one("shipping.methods", string="Logistics Company", )

    logistics_company_main = fields.Many2one(
        "shipping.methods",
        string="Logistics Company",
        compute="_compute_logistics_company_main",
        store=True,
        readonly=True,
    )

    notes_cit = fields.Char(string="Notes")
    packing_request = fields.Char(string="Packing Request")
    pickup_address = fields.Char(string="Pickup Address")
    delivery_address = fields.Char(string="Delivery Address")
    incoterms_cit = fields.Char(string="Incoterms")
    weight_cit = fields.Char(string="Weight")
    booking_number_cit = fields.Char(string="Booking Number")
    bol_status = fields.Boolean(string="BOL Status")
    shipment_status = fields.Char(string="Shipment Status")
    # charge_to_customer = fields.Float(string="Charge to Customer", store=True)
    charge_to_customer = fields.Float(
        string="Charge to Customer",
        compute="_compute_charge_to_customer",
        store=True,
        readonly=True,
    )

    document_attachment_ids = fields.Many2many(comodel_name='ir.attachment',
                                               string="Attachments", )

    # helper to find linked SO via origin field
    def _get_related_sale_order(self):
        self.ensure_one()
        if self.origin:
            return self.env["sale.order"].search([("name", "=", self.origin)], limit=1)
        return False

    # Syncing above fields to the fields of SO
    def _sync_to_sale_order(self):
        SaleOrder = self.env['sale.order']
        so_fields = SaleOrder._fields  # existing fields on this DB

        # Map PO -> SO fields (handle attachments separately)
        field_map = {
            "logistics_company_id": "logistics_company_so",
            "logistics_company_main": "so_logistics_company",
            "notes_cit": "notes_cit_so",
            "packing_request": "packing_request_so",
            "pickup_address": "pickup_address_so",
            "delivery_address": "delivery_address_so",
            "incoterms_cit": "incoterms_cit_so",
            "weight_cit": "weight_cit_so",
            "booking_number_cit": "booking_number_cit_so",
            "bol_status": "bol_status_so",
            "shipment_status": "shipment_status_so",
            "charge_to_customer": "charge_to_customer_so",
        }

        for po in self:
            so = po._get_related_sale_order()
            if not so:
                continue

            vals = {}
            for po_f, so_f in field_map.items():
                if so_f in so_fields:
                    val = getattr(po, po_f)
                    # M2O: write id; primitives write as is
                    vals[so_f] = val.id if hasattr(val, 'id') else val

            if 'document_attachment_so' in so_fields:
                vals['document_attachment_so'] = [(6, 0, po.document_attachment_ids.ids)]

            if vals:
                so.sudo().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_to_sale_order()
        return records

    def write(self, vals):  # Updating data to the fields
        res = super().write(vals)
        self._sync_to_sale_order()
        return res

    def unlink(self):
        SaleOrder = self.env['sale.order']
        so_fields = SaleOrder._fields
        for po in self:
            so = po._get_related_sale_order()
            if so:
                vals = {}
                mapping = {
                    "logistics_company_so": False,
                    "notes_cit_so": False,
                    "packing_request_so": False,
                    "pickup_address_so": False,
                    "delivery_address_so": False,
                    "incoterms_cit_so": False,
                    "weight_cit_so": False,
                    "booking_number_cit_so": False,
                    "bol_status_so": False,
                    "shipment_status_so": False,
                    "charge_to_customer_so": 0.0,
                }
                for so_f, default_val in mapping.items():
                    if so_f in so_fields:
                        vals[so_f] = default_val
                if 'document_attachment_so' in so_fields:
                    vals['document_attachment_so'] = [(5, 0, 0)]
                if vals:
                    so.sudo().write(vals)
        return super().unlink()

    # Make charge_to_customer a computed field that persists (set compute="_compute_charge_to_customer", store=True, readonly=True)
    @api.depends('logistics_company_id', 'logistics_ids.sub_shipping_id', 'logistics_ids.price')
    def _compute_charge_to_customer(self):
        for po in self:
            debug_hdr = f"[DEBUG][compute] PO({po.id})"
            if po.logistics_company_id:
                line = po.logistics_ids.filtered(lambda l: l.sub_shipping_id == po.logistics_company_id)[:1]
                if line:
                    print(
                        f"{debug_hdr} company={po.logistics_company_id.id} -> match line {line.id} price={line.price}")
                    po.charge_to_customer = line.price
                else:
                    print(
                        f"{debug_hdr} company={po.logistics_company_id.id} -> no matching logistics line; keep existing")
                    # keep existing value (do not reset)
            else:
                print(f"{debug_hdr} no logistics_company_id; keep existing")
                # keep existing value (do not reset)

    @api.depends('logistics_company_id', 'logistics_ids.sub_shipping_id', 'logistics_ids.shipping_method_id')
    def _compute_logistics_company_main(self):
        for po in self:
            debug_hdr = f"[DEBUG][compute_main] PO({po.id})"
            if po.logistics_company_id:
                line = po.logistics_ids.filtered(lambda l: l.sub_shipping_id == po.logistics_company_id)[:1]
                if line and line.shipping_method_id:
                    print(
                        f"{debug_hdr} company={po.logistics_company_id.id} -> match line {line.id} shipping_method={line.shipping_method_id.id}"
                    )
                    po.logistics_company_main = line.shipping_method_id
                else:
                    print(
                        f"{debug_hdr} company={po.logistics_company_id.id} -> no matching logistics line or missing shipping_method_id"
                    )
                    po.logistics_company_main = False
            else:
                print(f"{debug_hdr} no logistics_company_id; keep empty")
                po.logistics_company_main = False



class PurchaseOrderLogistics(models.Model):
    _name = 'purchase.order.logistics'
    _description = 'Purchase Order Logistics'

    order_id = fields.Many2one('purchase.order', ondelete='cascade', required=True)
    shipping_method_id = fields.Many2one('shipping.methods', string="Shipping Method", required=True)
    sub_shipping_id = fields.Many2one('sub.shipping', string="Logistics Company")
    price = fields.Float(string="Price Offered to Customer")


    company_email_cit = fields.Char(string="Company Email")
    origin_custom_clearance = fields.Char(string="Origin Custom Clearance")
    pickup_address_port = fields.Char(string="Pickup Address/Port")
    delivery_address_port = fields.Char(string="Delivery Address/Port")
    destination_customs_clearance = fields.Char(string="Destination Customs Clearance")
    price_quoted_ff = fields.Char(string="Price Quoted by FF")
    container_size_sea = fields.Char(string="Container Size if Sea")
    transit_time = fields.Float(string="Transit Time", help="Time in hours/days", digits=(16, 2))
    transit_time_cit = fields.Char(string="Transit Time",)
    quote_validation_date = fields.Date(string="Quote Validation Date")
