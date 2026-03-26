from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    stage_id = fields.Many2one(
        'purchase.stages',
        string='Stage',
        tracking=True,
        index=True,
        copy=False,
        group_expand='_read_group_stage_ids'
    )

    confirm_done = fields.Boolean(string='Confirmation Done', default=False, copy=False)

    STATE_STAGE_MAPPING = {
        'sent': 'Vendor Accepted Order',
        'cancel': 'Order Cancelled',
        'draft': 'Under Processing',
        'to approve': 'Needs Work',
        'purchase': 'Investigate Missing/Damaged Goods',
        'done': 'Order Completed',
    }

    STATE_SEQUENCE = [
        'sent',
        'cancel',
        'draft',
        'to approve',
        'purchase',
        'done',
    ]

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Make all stages visible in statusbar"""
        return stages.search([], order=order)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     """Set initial stage when creating purchase order"""
    #     # Ensure default stages exist
    #     # self.env['purchase.stages']._create_default_stages()
    #     self.env['purchase.stages']
    #
    #     records = super(PurchaseOrder, self).create(vals_list)
    #     for record in records:
    #         if record.state and not record.stage_id:
    #             record._sync_stage_from_state()
    #     return records

    @api.model_create_multi
    def create(self, vals_list):
        """Set initial stage WITHOUT linking to state"""
        records = super().create(vals_list)
        first_stage = self.env['purchase.stages'].search([], order='sequence, id', limit=1)
        if first_stage:
            for rec in records:
                if not rec.stage_id:
                    rec.stage_id = first_stage.id
        return records

    # def write(self, vals):
    #     """Sync stage when state changes and vice versa"""
    #     # Check if state is being changed
    #     if 'state' in vals and 'stage_id' not in vals:
    #         result = super(PurchaseOrder, self).write(vals)
    #         self._sync_stage_from_state()
    #         return result
    #
    #     # Check if stage is being changed
    #     if 'stage_id' in vals and 'state' not in vals:
    #         result = super(PurchaseOrder, self).write(vals)
    #         self._sync_state_from_stage()
    #         return result
    #
    #     return super(PurchaseOrder, self).write(vals)

    def write(self, vals):
        """No automatic sync between state and stage_id"""
        return super().write(vals)

    def _sync_stage_from_state(self):
        """Sync stage_id based on current state"""
        for record in self:
            if record.state in self.STATE_STAGE_MAPPING:
                stage_name = self.STATE_STAGE_MAPPING[record.state]
                stage = self.env['purchase.stages'].search([('name', '=', stage_name)], limit=1)
                if stage and record.stage_id != stage:
                    # Use super().write() to avoid recursion
                    super(PurchaseOrder, record).write({'stage_id': stage.id})

    def _sync_state_from_stage(self):
        """Sync state based on current stage_id"""
        for record in self:
            if record.stage_id:
                # Find the state that matches this stage name
                for state_key, stage_name in self.STATE_STAGE_MAPPING.items():
                    if record.stage_id.name == stage_name:
                        if record.state != state_key:
                            # Use super().write() to avoid recursion
                            super(PurchaseOrder, record).write({'state': state_key})
                        break

    # def action_next_stage_po(self):
    #     """Move to the next state."""
    #     for order in self:
    #         seq = self.STATE_SEQUENCE
    #         _logger.info(
    #             "[PO NEXT] PO(%s) current_state=%s sequence=%s",
    #             order.id, order.state, seq
    #         )
    #         if order.state not in seq:
    #             _logger.warning(
    #                 "[PO NEXT] PO(%s) state '%s' NOT in STATE_SEQUENCE",
    #                 order.id, order.state
    #             )
    #             continue
    #         idx = seq.index(order.state)
    #         if idx < len(seq) - 1:
    #             next_state = seq[idx + 1]
    #             _logger.info(
    #                 "[PO NEXT] PO(%s) moving %s → %s",
    #                 order.id, order.state, next_state
    #             )
    #             order.state = next_state
    #             # Sync will happen automatically through write() method
    #         else:
    #             _logger.info(
    #                 "[PO NEXT] PO(%s) already at LAST state (%s)",
    #                 order.id, order.state
    #             )

    def action_next_stage_po(self):
        stages = self.env['purchase.stages'].search([], order='sequence, id')
        stage_ids = stages.ids
        for po in self:
            if not stage_ids:
                continue
            if not po.stage_id:
                po.stage_id = stage_ids[0]
                continue
            if po.stage_id.id in stage_ids:
                idx = stage_ids.index(po.stage_id.id)
                if idx < len(stage_ids) - 1:
                    po.stage_id = stage_ids[idx + 1]

    # def action_previous_stage_po(self):
    #     """Move to the previous state."""
    #     for order in self:
    #         seq = self.STATE_SEQUENCE
    #
    #         _logger.info(
    #             "[PO PREV] PO(%s) current_state=%s sequence=%s",
    #             order.id, order.state, seq
    #         )
    #
    #         if order.state not in seq:
    #             _logger.warning(
    #                 "[PO PREV] PO(%s) state '%s' NOT in STATE_SEQUENCE",
    #                 order.id, order.state
    #             )
    #             continue
    #
    #         idx = seq.index(order.state)
    #
    #         if idx > 0:
    #             prev_state = seq[idx - 1]
    #             _logger.info(
    #                 "[PO PREV] PO(%s) moving %s → %s",
    #                 order.id, order.state, prev_state
    #             )
    #             order.state = prev_state
    #             # Sync will happen automatically through write() method
    #         else:
    #             _logger.info(
    #                 "[PO PREV] PO(%s) already at FIRST state (%s)",
    #                 order.id, order.state
    #             )

    def action_previous_stage_po(self):
        stages = self.env['purchase.stages'].search([], order='sequence, id')
        stage_ids = stages.ids
        for po in self:
            if not stage_ids:
                continue
            if not po.stage_id:
                po.stage_id = stage_ids[0]
                continue
            if po.stage_id.id in stage_ids:
                idx = stage_ids.index(po.stage_id.id)
                if idx > 0:
                    po.stage_id = stage_ids[idx - 1]

    def button_confirm(self):
        """Override button_confirm to set confirm_done to True"""
        result = super(PurchaseOrder, self).button_confirm()
        self.write({'confirm_done': True})
        return result

    def button_draft(self):
        """Override button_draft to set confirm_done to False"""
        result = super(PurchaseOrder, self).button_draft()
        self.write({'confirm_done': False})
        return result

    _AUTO_DONE_LOGISTICS = {'delivered_customer_ff', 'delivered_customer_warehouse', 'customer_picked_up'}

    @api.onchange('logistics_stage_po')
    def _onchange_logistics_stage_po_set_done(self):
        for po in self:
            if po.logistics_stage_po in self._AUTO_DONE_LOGISTICS:
                done_stage = self.env['purchase.stages'].sudo().search([('name', '=', 'Order Completed')], limit=1)
                if done_stage:
                    po.stage_id = done_stage

