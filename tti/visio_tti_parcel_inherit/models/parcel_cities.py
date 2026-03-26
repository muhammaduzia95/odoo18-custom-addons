from odoo import models, fields

class ParcelCities(models.Model):
    _name = 'parcel.cities'
    _description = 'Parcel Cities'

    name = fields.Char(string="City", required=True)
    country_id = fields.Many2one('res.country', string="Country", required=True)


class TtiParcels(models.Model):
    _inherit = 'tti.parcels'

    parcel_city_id = fields.Many2one('parcel.cities', string="Parcel City")