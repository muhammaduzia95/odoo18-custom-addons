
from odoo.exceptions import UserError
import requests
from odoo import models, fields, api, Command, _
import base64
from io import BytesIO
from PIL import Image
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    tti_is_kik_report = fields.Boolean(string="Is KIK Report", copy=False)
    tti_is_photo_lims = fields.Boolean(string="Is Logo Push to LIMS", copy=False)
    tti_lims_logo_report = fields.Many2one(
        'ir.attachment', ondelete='cascade', auto_join=True,
        copy=False, string="LIMS Report Logo",
    )
    tti_lims_logo_report_name = fields.Char(
        related='tti_lims_logo_report.name', readonly=False,
        string="LIMS Report Logo Name", copy=False
    )

    @api.model_create_multi
    def create(self, list_vals):
        partners = super(ResPartner, self).create(list_vals)
        for vals in list_vals:
            if vals.get('image_1920'):
                for partner in partners:
                   partner._create_image_attachment(vals['image_1920'])
        return partners


    def write(self, vals):
        res = super().write(vals)
        for partner in self:
            if vals.get('image_1920'):
                partner._create_image_attachment(vals['image_1920'])
        return res

    def _create_image_attachment(self, image_data):

        try:
            image_binary = base64.b64decode(image_data)
            if image_binary[:5] in [b"<?xml", b"<html", b"<svg ", b"{\"ver"]:
                return
            if isinstance(image_binary, bytes):
                image = Image.open(BytesIO(image_binary))
                image.verify()
                # Validate format
                allowed_formats = ['PNG', 'JPEG', 'JPG']
                image_format = image.format.upper()
                if image_format not in allowed_formats:
                    raise ValidationError(_("Only PNG, JPG, or JPEG formats are allowed."))

                attachment = self.env['ir.attachment'].create({
                    'name': f"{self.name} Logo.{image.format.lower()}",
                    'type': 'binary',
                    'datas': image_data,
                    'res_model': self._name,
                    'res_id': self.id,
                    'public': True,
                })
                if attachment:
                    self.sudo().write({
                        "tti_lims_logo_report": attachment.id,
                    })

        except Exception as e:
            raise ValidationError(_(f"Invalid image file.\n Error : {e}"))