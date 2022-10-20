# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 
from odoo.exceptions import UserError
import base64
import requests
import logging 
_logger = logging.getLogger(__name__)


class ProductCollection(models.Model): 
    _name = 'product.collection'
    _inherit = ['image.mixin']

    name = fields.Char()
    body_html = fields.Html()
    is_exported = fields.Boolean()
    company_ids = fields.Many2many('res.company', string="Companies")
    shopify_product_collection_ids = fields.One2many('shopify.product.collection', 'collection_id', string="Shopify Product Collection")
    image_url = fields.Char()
    
    @api.model
    def get_image_ept(self, url, verify=False):
        image_types = ["image/jpeg", "image/png", "image/tiff",
                       "image/vnd.microsoft.icon", "image/x-icon",
                       "image/vnd.djvu", "image/svg+xml", "image/gif"]
        response = requests.get(url, stream=True, verify=verify, timeout=10)
        if response.status_code == 200 and response.headers["Content-Type"] in image_types:
            image = base64.b64encode(response.content)
            if image:
                return image
        raise UserError(_("Can't find image.\nPlease provide valid Image URL."))
    
    @api.model
    def create(self, vals):
        verify = False
        ir_config_parameter_obj = self.env['ir.config_parameter']
        if not vals.get("image_1920", False) and vals.get("image_url", ""):
            if 'ssl_verify' in list(self.env.context.keys()):
                verify = True
            image = self.get_image_ept(vals.get("image_url"), verify=verify)
            vals.update({"image_1920": image})
        record = super(ProductCollection, self).create(vals)

        base_url = ir_config_parameter_obj.sudo().get_param('web.base.url')
        rec_id = str(record.id)
        url = base_url + '/cl/i/%s' % (base64.urlsafe_b64encode(rec_id.encode("utf-8")).decode("utf-8"))
        record.write({'image_url': url})
        return record

    
    #product_ids = fields.Many2many('product.template', string="Products")
    #shopify_collection_id = fields.Char("Shopify Collection ID")
    
class ShopifyProductCollection(models.Model): 
    _name = 'shopify.product.collection'
    _inherit = ['image.mixin']
    
    name = fields.Char()
    body_html = fields.Html()
    is_exported = fields.Boolean()

    company_id = fields.Many2one('res.company', string="Company")
    product_ids = fields.Many2many('product.template', string="Products")
    shopify_collection_id = fields.Char("Shopify Collection ID")
    image_url = fields.Char()
    
    collection_id = fields.Many2one('product.collection', company_dependent=True)
    