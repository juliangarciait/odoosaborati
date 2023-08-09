from odoo import api, fields, models
import requests

class ProductProductExport(models.Model):
    _inherit  = 'vex.product.product.conector'

    def export_vex(self):
        for record in self:
            if record.instance.conector == 'meli':
                self.env['meli.export'].export_product(record, None, False)

        res = super().export_vex()
        return res
