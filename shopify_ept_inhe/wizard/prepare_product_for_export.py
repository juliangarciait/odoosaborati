from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlsxwriter

#_logger = logging.getLogger("Shopify Layer")


class PrepareProductForExport(models.TransientModel):
    _inherit = "shopify.prepare.product.for.export.ept"

    def prepare_template_val_for_export_product_in_layer(self, product_template, shopify_instance, variant):
        res = super(PrepareProductForExport, self).prepare_template_val_for_export_product_in_layer(product_template, shopify_instance, variant)
        shopify_tags_ids = product_template.with_context(lang=shopify_instance.shopify_lang_id.code).shopify_tag_ids
        res.update({"tag_ids": shopify_tags_ids})
        return res