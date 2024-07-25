from odoo import models, fields, api, _
from odoo.addons.website.tools import get_video_embed_code
#from .. import shopify
#from ..shopify.pyactiveresource.connection import ClientError



class ShopifyProcessImportExport(models.TransientModel):
    _inherit = 'shopify.process.import.export'

    def manual_export_product_to_shopify(self):
        res = super(ShopifyProcessImportExport, self).manual_export_product_to_shopify()
        self.shopify_selective_product_stock_export()
        return res