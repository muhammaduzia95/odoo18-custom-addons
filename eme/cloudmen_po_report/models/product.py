from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Brand field with index for better search performance
    brand = fields.Char(
        string="Brand",
        index=True,
        help="Brand of the product"
    )

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """
        Override name search to include multiple fields in search operations:
        - name (product name)
        - x_studio_brand (studio brand field)
        - brand (brand field)
        - barcode
        - default_code (internal reference)
        This makes these fields searchable in Many2one fields, search bars, etc.
        """
        args = args or []
        domain = []

        if name:
            # Search in multiple fields using OR operator
            domain = [
                '|', '|', '|', '|',
                ('name', operator, name),
                ('x_studio_brand', operator, name),
                ('brand', operator, name),
                ('barcode', operator, name),
                ('default_code', operator, name)
            ]

        return self._search(domain + args, limit=limit, order=order, access_rights_uid=name_get_uid)

