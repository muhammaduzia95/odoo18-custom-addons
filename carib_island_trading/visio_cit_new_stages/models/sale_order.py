# D:\Visiomate\Odoo\odoo18\custom_addons\carib_island_trading\visio_cit_new_stages\models\sale_order.py
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    stage_id = fields.Many2one(
        'sale.stages',
        string='Stage',
        tracking=True,
        index=True,
        copy=False,
        group_expand='_read_group_stage_ids'
    )

    confirm_done = fields.Boolean(string='Confirmation Done', default=False, copy=False)
    cancel_done = fields.Boolean(string='Cancel Done', default=False, copy=False)

    def action_confirm(self):
        """Override action_confirm to set confirm_done to True"""
        result = super(SaleOrder, self).action_confirm()
        self.write({'confirm_done': True})
        return result

    def action_draft(self):
        """Override action_draft to set confirm_done to False"""
        result = super(SaleOrder, self).action_draft()
        self.write({'confirm_done': False})
        return result

    STATE_STAGE_MAPPING = {
        'draft': 'Request Deposit',
        'request_balance': 'Request Balance Payment',
        'sent': 'Share Invoice',
        'sale': 'Request Order Confirmation',
        'share_logistic_docs': 'Share Logistic Documents',
        'request_payment_receipt': 'Request Payment Receipt',
        'check_payment_received': 'Check if Payment Was Received',
        'share_credit_note': 'Share Credit Note',
        'cancel': 'Investigate Missing / Damaged Goods',
    }

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Make all stages visible in statusbar"""
        return stages.search([], order=order)

    # def write(self, vals):
    #     """Sync stage when state changes and vice versa"""
    #     # Check if state is being changed
    #     if 'state' in vals and 'stage_id' not in vals:
    #         result = super(SaleOrder, self).write(vals)
    #         self._sync_stage_from_state()
    #         return result
    #
    #     # if 'stage_id' in vals and 'state' not in vals:
    #     #     result = super(SaleOrder, self).write(vals)
    #     #     self._sync_state_from_stage()
    #     #     return result
    #
    #     return super(SaleOrder, self).write(vals)

    def write(self, vals):
        """No automatic sync between state and stage_id"""
        return super(SaleOrder, self).write(vals)

    def _sync_stage_from_state(self):
        """Sync stage_id based on current state"""
        for record in self:
            if record.state in self.STATE_STAGE_MAPPING:
                stage_name = self.STATE_STAGE_MAPPING[record.state]
                stage = self.env['sale.stages'].search([('name', '=', stage_name)], limit=1)
                if stage and record.stage_id != stage:
                    # Use super().write() to avoid recursion
                    super(SaleOrder, record).write({'stage_id': stage.id})

    def _sync_state_from_stage(self):
        """Sync state based on current stage_id"""
        for record in self:
            if record.stage_id:
                # Find the state that matches this stage name
                for state_key, stage_name in self.STATE_STAGE_MAPPING.items():
                    if record.stage_id.name == stage_name:
                        if record.state != state_key:
                            # Use super().write() to avoid recursion
                            super(SaleOrder, record).write({'state': state_key})
                        break

    # def action_next_stage_so(self):
    #     for order in self:
    #         seq = order.STATE_SEQUENCE
    #         if order.state in seq:
    #             idx = seq.index(order.state)
    #             if idx < len(seq) - 1:
    #                 order.state = seq[idx + 1]
    #                 # Sync will happen automatically through write() method

    def action_next_stage_so(self):
        stages = self.env['sale.stages'].search([], order='sequence, id')
        stage_ids = stages.ids
        for order in self:
            if not stage_ids:
                continue
            if not order.stage_id:
                order.stage_id = stage_ids[0]
                continue
            if order.stage_id.id in stage_ids:
                idx = stage_ids.index(order.stage_id.id)
                if idx < len(stage_ids) - 1:
                    order.stage_id = stage_ids[idx + 1]

    # def action_previous_stage_so(self):
    #     for order in self:
    #         seq = order.STATE_SEQUENCE
    #         if order.state in seq:
    #             idx = seq.index(order.state)
    #             if idx > 0:
    #                 order.state = seq[idx - 1]
    #                 # Sync will happen automatically through write() method

    def action_previous_stage_so(self):
        stages = self.env['sale.stages'].search([], order='sequence, id')
        stage_ids = stages.ids
        for order in self:
            if not stage_ids:
                continue
            if not order.stage_id:
                order.stage_id = stage_ids[0]
                continue
            if order.stage_id.id in stage_ids:
                idx = stage_ids.index(order.stage_id.id)
                if idx > 0:
                    order.stage_id = stage_ids[idx - 1]

    def _action_cancel(self):
        inv = self.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        inv.button_cancel()
        return self.write({'state': 'cancel', 'cancel_done': True})