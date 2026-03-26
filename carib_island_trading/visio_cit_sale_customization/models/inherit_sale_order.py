# visio_cit_sale_customization/models/inherit_sale_order.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_create_purchase_request(self):
        self.ensure_one()
        print("\n[action_create_purchase_request] START")
        print(f"[action_create_purchase_request] order id={self.id} name={self.name} note={self.note!r}")

        vals = {'sale_order_id': self.id, 'note_pr': self.note}
        print(f"[action_create_purchase_request] create purchase.request vals={vals}")

        pr = self.env['purchase.request'].create(vals)
        print(f"[action_create_purchase_request] CREATED purchase.request id={pr.id} display_name={pr.display_name}")

        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Purchase Request Created",
                'message': f"Purchase Request for {self.name} has been created.",
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                },
            },
        }
        print(f"[action_create_purchase_request] RETURN action={action}")
        print("[action_create_purchase_request] END\n")
        return action

    def action_view_purchase_order(self):
        self.ensure_one()
        print("\n[action_view_purchase_order] START")
        print(f"[action_view_purchase_order] order id={self.id} name={self.name}")

        action = self.env.ref('purchase.action_rfq').read()[0]
        print(f"[action_view_purchase_order] base action (before domain) keys={list(action.keys())}")

        action['domain'] = [('origin', '=', self.name)]
        print(f"[action_view_purchase_order] set domain={action['domain']}")
        print("[action_view_purchase_order] END\n")
        return action

    markup_percent = fields.Integer(string="Markup (%)", help="Enter the markup percentage to apply on this order.")
    margin_percent = fields.Integer(string="Margin (%)", help="Enter the margin percentage to apply on this order.")

    logistics_ids = fields.One2many('sale.order.logistics', 'order_id', string="Logistics")

    @api.onchange('markup_percent', 'margin_percent')
    def _onchange_percent_propagate(self):
        print("\n[_onchange_percent_propagate] START")
        for order in self:
            print(f"[_onchange_percent_propagate] order id={order.id} name={order.name} "
                  f"markup_percent={order.markup_percent} margin_percent={order.margin_percent} "
                  f"lines_count={len(order.order_line)}")

            for line in order.order_line:
                print(f"[_onchange_percent_propagate] -> line id={line.id} product={line.product_id.display_name} "
                      f"BEFORE markup_percent_line={getattr(line, 'markup_percent_line', None)} "
                      f"margin_percent_line={getattr(line, 'margin_percent_line', None)}")

                line.markup_percent_line = order.markup_percent
                line.margin_percent_line = order.margin_percent

                print(
                    f"[_onchange_percent_propagate] -> line id={line.id} AFTER  markup_percent_line={line.markup_percent_line} "
                    f"margin_percent_line={line.margin_percent_line}")

        print("[_onchange_percent_propagate] END\n")

    purchase_order_count = fields.Integer(
        string="Purchase Orders", compute='_compute_purchase_order_count')

    def _compute_purchase_order_count(self):
        print("\n[_compute_purchase_order_count] START")
        for rec in self:
            domain = [('origin', '=', rec.name)]
            print(f"[_compute_purchase_order_count] rec id={rec.id} name={rec.name} domain={domain}")

            count = self.env['purchase.order'].search_count(domain)
            print(f"[_compute_purchase_order_count] -> count={count}")

            rec.purchase_order_count = count
        print("[_compute_purchase_order_count] END\n")

    def action_view_purchase_orders(self):
        self.ensure_one()
        print("\n[action_view_purchase_orders] START")
        print(f"[action_view_purchase_orders] order id={self.id} name={self.name}")

        action = {
            'name': "Related Purchase Orders",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('origin', '=', self.name)],
            'context': {'default_origin': self.name},
        }
        print(f"[action_view_purchase_orders] RETURN action={action}")
        print("[action_view_purchase_orders] END\n")
        return action

    attachment_ids_so = fields.Many2many('ir.attachment', string='Attachments', )

    po_state = fields.Char(string="PO State", compute='_compute_po_state', readonly=True)

    # def _compute_po_state(self):
    #     print("\n[_compute_po_state] START")
    #     for order in self:
    #         print(f"[_compute_po_state] order id={order.id} name={order.name}")
    #
    #         purchase_orders = self.env['purchase.order'].search([('origin', '=', order.name)])
    #         print(f"[_compute_po_state] found purchase_orders ids={purchase_orders.ids}")
    #
    #         # purchase.order doesn't have stage_id in standard Odoo -> use 'state'
    #         states = purchase_orders.mapped('state')
    #         print(f"[_compute_po_state] states(raw)={states}")
    #
    #         # Optional: map technical states to nicer labels
    #         state_map = {
    #             'draft': 'RFQ',
    #             'sent': 'RFQ Sent',
    #             'to approve': 'To Approve',
    #             'purchase': 'Purchase Order',
    #             'done': 'Locked',
    #             'cancel': 'Cancelled',
    #         }
    #         labels = [state_map.get(s, s) for s in states]
    #         print(f"[_compute_po_state] labels(mapped)={labels}")
    #
    #         order.po_state = ', '.join(sorted(set(labels))) if labels else 'No PO Against this Sale Order'
    #         print(f"[_compute_po_state] computed po_state={order.po_state!r}")
    #
    #     print("[_compute_po_state] END\n")

    def _compute_po_state(self):
        print("\n[_compute_po_state] START")
        for order in self:
            print(f"[_compute_po_state] order id={order.id} name={order.name}")

            purchase_orders = self.env['purchase.order'].search([('origin', '=', order.name)])
            print(f"[_compute_po_state] found purchase_orders ids={purchase_orders.ids}")

            labels = purchase_orders.mapped('stage_id.name')
            labels = [label for label in labels if label]
            print(f"[_compute_po_state] labels={labels}")

            order.po_state = ', '.join(sorted(set(labels))) if labels else 'No PO Against this Sale Order'
            print(f"[_compute_po_state] computed po_state={order.po_state!r}")

        print("[_compute_po_state] END\n")

    quote_validation_cit = fields.Date(string="Quote Validation Date")
    purchase_request_ids = fields.One2many(
        'purchase.request', 'sale_order_id',
        string='Purchase Requests',
        readonly=True,
    )
    purchase_request_created = fields.Boolean(
        string="Purchase Request Created",
        compute='_compute_purchase_request_created',
        store=True,
    )

    @api.depends('purchase_request_ids')
    def _compute_purchase_request_created(self):
        print("\n[_compute_purchase_request_created] START")
        for order in self:
            print(f"[_compute_purchase_request_created] order id={order.id} name={order.name} "
                  f"purchase_request_ids={order.purchase_request_ids.ids}")

            order.purchase_request_created = bool(order.purchase_request_ids)
            print(f"[_compute_purchase_request_created] -> purchase_request_created={order.purchase_request_created}")

        print("[_compute_purchase_request_created] END\n")

    # note field on sale order should not be added in narration on invoice
    def _prepare_invoice(self):
        print("\n[_prepare_invoice] START")
        print(f"[_prepare_invoice] order id={self.id} name={self.name}")

        vals = super()._prepare_invoice()
        print(f"[_prepare_invoice] vals from super keys={list(vals.keys())}")

        narration_before = vals.get('narration', None)
        print(f"[_prepare_invoice] narration BEFORE pop={narration_before!r}")

        vals.pop('narration', None)  # or: vals['narration'] = False

        narration_after = vals.get('narration', None)
        print(f"[_prepare_invoice] narration AFTER pop={narration_after!r}")
        print("[_prepare_invoice] END\n")
        return vals

    # Sale Order/ Notebook/ Page/ Fields
    logistics_company_so = fields.Many2one("sub.shipping", string="Logistics Company")
    so_logistics_company = fields.Many2one("shipping.methods", string="Logistics Company")
    notes_cit_so = fields.Char(string="Notes")
    packing_request_so = fields.Char(string="Packing Request")
    pickup_address_so = fields.Char(string="Pickup Address")
    delivery_address_so = fields.Char(string="Delivery Address")
    incoterms_cit_so = fields.Char(string="Incoterms")
    weight_cit_so = fields.Char(string="Weight")
    booking_number_cit_so = fields.Char(string="Booking Number")
    bol_status_so = fields.Boolean(string="BOL Status")
    shipment_status_so = fields.Char(string="Shipment Status")
    charge_to_customer_so = fields.Float(string="Charge to Customer")
    document_attachment_so = fields.Many2many(
        'ir.attachment',
        'sale_order_ir_attachments_rel',
        'sale_order_id',
        'attachment_id',
        string="Attachments"
    )

    logistics_details_accepted = fields.Boolean(string="Logistics Details Accepted", default=False, copy=False)

    def _ensure_logistics_details_line(self):
        """ Add or update a sale.order.line for the logistics company
        with the charge_to_customer_so price. """
        print("\n[_ensure_logistics_details_line] START")
        for order in self:
            print(f"[_ensure_logistics_details_line] order id={order.id} name={order.name} "
                  f"so_logistics_company={order.so_logistics_company.display_name if order.so_logistics_company else None} "
                  f"charge_to_customer_so={order.charge_to_customer_so}")

            if not order.so_logistics_company:
                print("[_ensure_logistics_details_line] ERROR: so_logistics_company not set -> raising UserError")
                raise UserError(_("Please select a Logistics Company first."))

            domain = [('name', '=', order.so_logistics_company.name)]
            print(f"[_ensure_logistics_details_line] searching product.product domain={domain}")
            product = self.env['product.product'].search(domain, limit=1)
            print(f"[_ensure_logistics_details_line] found product id={product.id if product else None} "
                  f"name={product.name if product else None}")

            if not product:
                msg = _(
                    "No product found with name '%s' (needed for logistics line).") % order.so_logistics_company.name
                print(f"[_ensure_logistics_details_line] ERROR: {msg} -> raising UserError")
                raise UserError(msg)

            print(f"[_ensure_logistics_details_line] scanning existing lines for product_id={product.id}")
            so_line = order.order_line.filtered(lambda l: l.product_id == product)[:1]
            print(f"[_ensure_logistics_details_line] matched so_line id={so_line.id if so_line else None}")

            if so_line:
                print(f"[_ensure_logistics_details_line] updating existing line id={so_line.id} "
                      f"price_unit BEFORE={so_line.price_unit} -> AFTER={order.charge_to_customer_so}")
                # update existing line
                so_line.price_unit = order.charge_to_customer_so
                print(
                    f"[_ensure_logistics_details_line] updated existing line id={so_line.id} price_unit NOW={so_line.price_unit}")
            else:
                vals = {
                    'order_id': order.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': 1,
                    'product_uom': product.uom_id.id,
                    'price_unit': order.charge_to_customer_so or 0.0,
                }
                print(f"[_ensure_logistics_details_line] creating new sale.order.line vals={vals}")
                # create new line
                new_line = order.order_line.create(vals)
                print(
                    f"[_ensure_logistics_details_line] CREATED new line id={new_line.id} price_unit={new_line.price_unit}")

            # Helpful snapshot of totals after line ensure (doesn't change logic)
            print(f"[_ensure_logistics_details_line] totals snapshot: amount_untaxed={order.amount_untaxed} "
                  f"amount_tax={order.amount_tax} amount_total={order.amount_total}")

        print("[_ensure_logistics_details_line] END\n")

    def action_accept_logistics_details(self):
        print("\n[action_accept_logistics_details] START")
        for order in self:
            print(f"[action_accept_logistics_details] order id={order.id} name={order.name} "
                  f"charge_to_customer_so={order.charge_to_customer_so} "
                  f"logistics_details_accepted BEFORE={order.logistics_details_accepted}")

            if not order.charge_to_customer_so or order.charge_to_customer_so <= 0:
                print(
                    "[action_accept_logistics_details] ERROR: charge_to_customer_so invalid -> raising ValidationError")
                raise ValidationError(_("Charge to Customer should be greater than 0"))

            print("[action_accept_logistics_details] calling _ensure_logistics_details_line()")
            order._ensure_logistics_details_line()

            order.logistics_details_accepted = True
            print(
                f"[action_accept_logistics_details] logistics_details_accepted AFTER={order.logistics_details_accepted}")

            # Helpful snapshot of totals after acceptance (doesn't change logic)
            print(f"[action_accept_logistics_details] totals snapshot: amount_untaxed={order.amount_untaxed} "
                  f"amount_tax={order.amount_tax} amount_total={order.amount_total}")

        print("[action_accept_logistics_details] END\n")
        return True


class SaleOrderLogistics(models.Model):
    _name = 'sale.order.logistics'
    _description = 'Sale Order Logistics'

    order_id = fields.Many2one('sale.order', string="Sale Order", ondelete='cascade', required=True)
    shipping_method_id = fields.Many2one('shipping.methods', string="Shipping Method", required=True)
    sub_shipping_id = fields.Many2one('sub.shipping', string="Sub Shipping")
    price = fields.Float(string="Price")
    accepted_by_customer = fields.Boolean(string="Accepted by Customer")

    charge_to_customer_synced = fields.Boolean(default=False, copy=False)  # this field is for syncing purpose

    def _ensure_shipping_product_line(self):
        """
        Find (or create) a sale.order.line on the parent SO that
        represents this shipping method, and set its price.
        """
        for l in self:
            order = l.order_id
            product = l.env['product.product'].search(
                [('name', '=', l.shipping_method_id.name)], limit=1
            )
            if not product:
                raise UserError(
                    _("No product found with name '%s' (needed for shipping line).")
                    % l.shipping_method_id.name
                )

            so_line = order.order_line.filtered(lambda x: x.product_id == product)[:1]
            if so_line:
                so_line.price_unit = l.price
            else:
                order.order_line.create({
                    'order_id': order.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': 1,
                    'product_uom': product.uom_id.id,
                    'price_unit': l.price,
                })

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get('accepted_by_customer'):
            record._ensure_shipping_product_line()
        return record

    def write(self, vals):
        res = super().write(vals)
        if 'accepted_by_customer' in vals and vals['accepted_by_customer']:
            for rec in self:
                rec._ensure_shipping_product_line()
        elif {'price', 'shipping_method_id'}.intersection(vals) and self.filtered('accepted_by_customer'):
            for rec in self.filtered('accepted_by_customer'):
                rec._ensure_shipping_product_line()
        return res

    def action_accept_logistics(self):
        for rec in self:
            rec.accepted_by_customer = True
        return True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    markup_percent_line = fields.Integer(string="Markup (%)")
    margin_percent_line = fields.Integer(string="Margin (%)")

    # @api.depends(
    #     'product_uom_qty', 'discount', 'price_unit', 'tax_id',
    #     'order_id.currency_id', 'order_id.partner_id',
    #     'markup_percent_line', 'margin_percent_line'
    # )
    # def _compute_amount(self):
    #     # first keep Odoo default result for normal lines
    #     super()._compute_amount()
    #
    #     for line in self:
    #         # skip section/note lines
    #         if getattr(line, 'display_type', False):
    #             continue
    #
    #         if not (line.markup_percent_line or line.margin_percent_line):
    #             continue
    #
    #         base = line.price_unit or 0.0  # CS Price (must remain unchanged)
    #         qty = line.product_uom_qty or 0.0
    #
    #         # IMPORTANT: Odoo discount is percent (10 = 10%), so divide by 100
    #         disc_pct = line.discount or 0.0
    #         disc_factor = 1.0 - (disc_pct / 100.0)
    #
    #         mk_pct = line.markup_percent_line or 0.0
    #         mg_pct = line.margin_percent_line or 0.0
    #
    #         # ---- compute unit price by your formulas (but with % as /100) ----
    #         price_markup = None
    #         if mk_pct:
    #             markup_value = base * (mk_pct / 100.0)
    #             price_markup = base + markup_value
    #
    #         price_margin = None
    #         if mg_pct:
    #             margin_cal = 1.0 - (mg_pct / 100.0)  # (100 - margin)% => divide by 100
    #             if margin_cal <= 0:
    #                 raise ValidationError(_("Margin must be less than 100%."))
    #             price_margin = base / margin_cal
    #
    #         # BOTH -> show difference in subtotal (as you asked earlier)
    #         if mk_pct and mg_pct:
    #             effective_unit = abs(price_margin - price_markup)
    #             mode = "BOTH(DIFF)"
    #         elif mg_pct:
    #             effective_unit = price_margin
    #             mode = "MARGIN"
    #         else:
    #             effective_unit = price_markup
    #             mode = "MARKUP"
    #
    #         # apply discount (same as your “After Discount Value” logic)
    #         effective_unit_after_disc = (effective_unit or 0.0) * disc_factor
    #
    #         print("\n[_compute_amount CUSTOM] line id=", line.id, "mode=", mode)
    #         print("  CS price_unit(base)=", base, "qty=", qty, "discount%=", disc_pct)
    #         print("  markup%=", mk_pct, "margin%=", mg_pct)
    #         print("  price_markup=", price_markup, "price_margin=", price_margin)
    #         print("  effective_unit(before disc)=", effective_unit)
    #         print("  effective_unit(after disc)=", effective_unit_after_disc)
    #
    #         # taxes + totals
    #         if line.tax_id:
    #             taxes_res = line.tax_id.compute_all(
    #                 effective_unit_after_disc,
    #                 currency=line.order_id.currency_id,
    #                 quantity=qty,
    #                 product=line.product_id,
    #                 partner=line.order_id.partner_id,
    #             )
    #             subtotal = taxes_res['total_excluded']
    #             total = taxes_res['total_included']
    #         else:
    #             subtotal = effective_unit_after_disc * qty
    #             total = subtotal
    #
    #         line.price_subtotal = subtotal
    #         line.price_total = total
    #         line.price_tax = total - subtotal
    #
    #         print("  RESULT subtotal=", line.price_subtotal, "tax=", line.price_tax, "total=", line.price_total)

    def _cit_effective_unit_before_discount(self):
        """Return YOUR selling unit price (before discount)."""
        self.ensure_one()

        base = self.price_unit or 0.0  # CS Price (must remain unchanged)
        mk_pct = self.markup_percent_line or 0.0
        mg_pct = self.margin_percent_line or 0.0

        price_markup = base
        if mk_pct:
            price_markup = base + (base * (mk_pct / 100.0))

        price_margin = base
        if mg_pct:
            margin_cal = 1.0 - (mg_pct / 100.0)
            if margin_cal <= 0:
                raise ValidationError(_("Margin must be less than 100%."))
            price_margin = base / margin_cal

        # YOUR rule when BOTH are set
        if mk_pct and mg_pct:
            return abs(price_margin - price_markup)
        elif mg_pct:
            return price_margin
        elif mk_pct:
            return price_markup
        return base

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """
        Odoo 18 uses THIS dict to compute:
        - line subtotal/tax/total
        - order totals widget (Untaxed/Tax/Total)
        """
        self.ensure_one()
        base_line = super()._prepare_base_line_for_taxes_computation(**kwargs)

        # skip section/note lines
        if getattr(self, 'display_type', False):
            return base_line

        if self.markup_percent_line or self.margin_percent_line:
            effective_unit = self._cit_effective_unit_before_discount()

            # IMPORTANT: don't apply discount here. Odoo applies discount itself.
            base_line['price_unit'] = effective_unit

            print("\n[CIT base_line override] line", self.id,
                  "CS price_unit=", self.price_unit,
                  "effective_unit=", effective_unit,
                  "discount%=", self.discount,
                  "qty=", self.product_uom_qty)

        return base_line

    @api.depends(
        'product_uom_qty', 'discount', 'price_unit', 'tax_id',
        'markup_percent_line', 'margin_percent_line'
    )
    def _compute_amount(self):
        print("[DEBUG] Entering _compute_amount")
        for line in self:
            print(f"[DEBUG] Computing amount for line ID: {line.id}, "
                  f"qty={line.product_uom_qty}, price_unit={line.price_unit}, "
                  f"discount={line.discount}, markup={line.markup_percent_line}, "
                  f"margin={line.margin_percent_line}")
        # DO NOT custom compute taxes here.
        # Our base_line override makes Odoo compute correct values everywhere.
        result = super()._compute_amount()
        print("[DEBUG] Finished _compute_amount")
        return result

    def _prepare_invoice_line(self, **optional_values):
        """Copy markup/margin fields from SO line to invoice line."""
        print("\n[DEBUG][SO->_prepare_invoice_line] START")
        self.ensure_one()

        print(
            f"[DEBUG][SO->_prepare_invoice_line] so_line_id={self.id} "
            f"product={self.product_id.display_name} "
            f"price_unit={self.price_unit} discount={self.discount} "
            f"markup_percent_line={self.markup_percent_line} "
            f"margin_percent_line={self.margin_percent_line}"
        )

        vals = super()._prepare_invoice_line(**optional_values)

        print(f"[DEBUG][SO->_prepare_invoice_line] vals from super BEFORE={vals}")

        # IMPORTANT: use invoice field names here
        vals['markup_percent_line_inv'] = self.markup_percent_line or 0
        vals['margin_percent_line_inv'] = self.margin_percent_line or 0

        print(
            f"[DEBUG][SO->_prepare_invoice_line] copied to invoice vals -> "
            f"markup_percent_line_inv={vals.get('markup_percent_line_inv')} "
            f"margin_percent_line_inv={vals.get('margin_percent_line_inv')}"
        )
        print(f"[DEBUG][SO->_prepare_invoice_line] vals from super AFTER={vals}")
        print("[DEBUG][SO->_prepare_invoice_line] END\n")

        return vals
