# carib_island_trading\visio_cit_sale_customization\models\inherit_account_move.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    attachment_ids_in = fields.Many2many('ir.attachment', string='Attachments', )


    def _prepare_product_base_line_for_taxes_computation(self, line):
        print("\n[DEBUG][AccountMove->_prepare_product_base_line_for_taxes_computation] START")
        print(
            f"[DEBUG][AccountMove] move_id={self.id} "
            f"line_id={line.id} display_type={line.display_type} "
            f"price_unit={line.price_unit} quantity={line.quantity} discount={line.discount} "
            f"markup_inv={getattr(line, 'markup_percent_line_inv', None)} "
            f"margin_inv={getattr(line, 'margin_percent_line_inv', None)}"
        )

        base_line = super()._prepare_product_base_line_for_taxes_computation(line)
        print(f"[DEBUG][AccountMove] base_line from super={base_line}")

        if line.display_type not in ('product', 'cogs'):
            print("[DEBUG][AccountMove] skipped because not product/cogs")
            print("[DEBUG][AccountMove->_prepare_product_base_line_for_taxes_computation] END\n")
            return base_line

        if line.markup_percent_line_inv or line.margin_percent_line_inv:
            effective_unit = line._cit_effective_unit_before_discount_inv()
            base_line['price_unit'] = effective_unit

            print(
                f"[DEBUG][AccountMove] overriding base_line['price_unit'] "
                f"from {line.price_unit} to {effective_unit}"
            )
        else:
            print("[DEBUG][AccountMove] no markup/margin on invoice line, no override")

        print(f"[DEBUG][AccountMove] final base_line={base_line}")
        print("[DEBUG][AccountMove->_prepare_product_base_line_for_taxes_computation] END\n")
        return base_line


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    markup_percent_line_inv = fields.Integer(string="Markup (%)")
    margin_percent_line_inv = fields.Integer(string="Margin (%)")

    def _cit_effective_unit_before_discount_inv(self):
        print("\n[DEBUG][AML->_cit_effective_unit_before_discount_inv] START")
        self.ensure_one()

        base = self.price_unit or 0.0
        mk_pct = self.markup_percent_line_inv or 0.0
        mg_pct = self.margin_percent_line_inv or 0.0

        print(
            f"[DEBUG][AML] line_id={self.id} product={self.product_id.display_name} "
            f"base={base} mk_pct={mk_pct} mg_pct={mg_pct}"
        )

        price_markup = base
        if mk_pct:
            price_markup = base + (base * (mk_pct / 100.0))
            print(f"[DEBUG][AML] price_markup={price_markup}")
        else:
            print("[DEBUG][AML] markup not applied")

        price_margin = base
        if mg_pct:
            margin_cal = 1.0 - (mg_pct / 100.0)
            print(f"[DEBUG][AML] margin_cal={margin_cal}")

            if margin_cal <= 0:
                print("[DEBUG][AML] invalid margin, raising ValidationError")
                raise ValidationError(_("Margin must be less than 100%."))

            price_margin = base / margin_cal
            print(f"[DEBUG][AML] price_margin={price_margin}")
        else:
            print("[DEBUG][AML] margin not applied")

        if mk_pct and mg_pct:
            result = abs(price_margin - price_markup)
            print(f"[DEBUG][AML] BOTH applied -> result={result}")
        elif mg_pct:
            result = price_margin
            print(f"[DEBUG][AML] ONLY MARGIN -> result={result}")
        elif mk_pct:
            result = price_markup
            print(f"[DEBUG][AML] ONLY MARKUP -> result={result}")
        else:
            result = base
            print(f"[DEBUG][AML] DEFAULT BASE -> result={result}")

        print("[DEBUG][AML->_cit_effective_unit_before_discount_inv] END\n")
        return result

    @api.depends(
        'quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id',
        'markup_percent_line_inv', 'margin_percent_line_inv'
    )
    def _compute_totals(self):
        print("\n[DEBUG][AML->_compute_totals] START")
        for line in self:
            print(
                f"[DEBUG][AML->_compute_totals][BEFORE] line_id={line.id} "
                f"product={line.product_id.display_name} display_type={line.display_type} "
                f"qty={line.quantity} price_unit={line.price_unit} discount={line.discount} "
                f"markup_inv={line.markup_percent_line_inv} margin_inv={line.margin_percent_line_inv} "
                f"subtotal={line.price_subtotal} total={line.price_total}"
            )

        res = super()._compute_totals()

        for line in self:
            print(
                f"[DEBUG][AML->_compute_totals][AFTER] line_id={line.id} "
                f"product={line.product_id.display_name} "
                f"subtotal={line.price_subtotal} total={line.price_total}"
            )

        print("[DEBUG][AML->_compute_totals] END\n")
        return res
