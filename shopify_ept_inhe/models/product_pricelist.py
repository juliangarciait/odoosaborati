from odoo import models, fields, api, _
import logging 
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model): 
    _inherit = 'product.pricelist.item'

    def write(self, values):
        res = super(ProductPricelistItem, self).write(values)
        shopify_instances = self.env['shopify.instance.ept'].sudo().search([('shopify_company_id','=',self.company_id.id),('shopify_pricelist_id','=', self.pricelist_id.id)])
        if not shopify_instances:
            shopify_instances = self.env['shopify.instance.ept'].sudo().search([('shopify_company_id','=',self.company_id.id),('shopify_compare_pricelist_id','=', self.pricelist_id.id)])
        if shopify_instances:
            shopify_product_template = self.env['shopify.product.template.ept'].sudo().search([('product_tmpl_id','=',self.product_tmpl_id.id),('shopify_instance_id','=',shopify_instances.id)])
            for product in shopify_product_template:
                process_import_export_obj = self.env['shopify.process.import.export'].sudo().create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
                if process_import_export_obj: 
                    process_import_export_obj.shopify_is_set_price = True
                    process_import_export_obj.with_context({'active_ids' : [product.id]}).sudo().manual_update_product_to_shopify()
        return res
    

    def unlink(self):
        pricelist_id = self.pricelist_id.id
        company_id = self.company_id.id
        product_tmp_id = self.product_tmpl_id.id
        res = super(ProductPricelistItem, self).unlink()
        shopify_instances = self.env['shopify.instance.ept'].sudo().search([('shopify_company_id','=',company_id ),('shopify_pricelist_id','=', pricelist_id)])
        if not shopify_instances:
            shopify_instances = self.env['shopify.instance.ept'].sudo().search([('shopify_company_id','=',company_id ),('shopify_compare_pricelist_id','=', pricelist_id)])
        if shopify_instances:
            shopify_product_template = self.env['shopify.product.template.ept'].sudo().search([('product_tmpl_id','=',product_tmp_id),('shopify_instance_id','=',shopify_instances.id)])
            for product in shopify_product_template:
                process_import_export_obj = self.env['shopify.process.import.export'].sudo().create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
                if process_import_export_obj: 
                    process_import_export_obj.shopify_is_set_price = True
                    process_import_export_obj.with_context({'active_ids' : [product.id]}).sudo().manual_update_product_to_shopify()
        return res
    

    @api.model
    def create(self, vals_list):
        res = super(ProductPricelistItem, self).create(vals_list)
        shopify_instances = self.env['shopify.instance.ept'].sudo().search([('shopify_company_id','=',res.company_id.id),('shopify_pricelist_id','=', res.pricelist_id.id)])
        if not shopify_instances:
            shopify_instances = self.env['shopify.instance.ept'].sudo().search([('shopify_company_id','=',res.company_id.id),('shopify_compare_pricelist_id','=', res.pricelist_id.id)])
        if shopify_instances:
            shopify_product_template = self.env['shopify.product.template.ept'].sudo().search([('product_tmpl_id','=',res.product_tmpl_id.id),('shopify_instance_id','=',shopify_instances.id)])
            for product in shopify_product_template:
                process_import_export_obj = self.env['shopify.process.import.export'].sudo().create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
                if process_import_export_obj: 
                    process_import_export_obj.shopify_is_set_price = True
                    process_import_export_obj.with_context({'active_ids' : [product.id]}).sudo().manual_update_product_to_shopify()
        return res
    
        #shopify_pricelist_id
        #shopify_compare_pricelist_id
        #pricelist_id
        
        