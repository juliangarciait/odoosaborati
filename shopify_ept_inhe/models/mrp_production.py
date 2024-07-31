from odoo import models, api, fields, _ 

class MrpProduction(models.Model): 
    _inherit = 'mrp.production'
    
    def button_mark_done(self): 
        res = super(MrpProduction, self).button_mark_done()
        lista_de_productos = [self.product_id.product_tmpl_id.id]
        for prod_component in self.move_raw_ids.product_id.product_tmpl_id.ids:
                lista_de_productos.append(prod_component)

        if len(lista_de_productos)== 1:
                shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.product_id.product_tmpl_id.id)])
        else:
                shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','in',lista_de_productos)])

        for product in shopify_product_template: 
            process_import_export_obj = False
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : product.shopify_instance_id.id,
            })

            if process_import_export_obj: 
                process_import_export_obj.with_context({'active_ids' : [product.id]}).shopify_selective_product_stock_export()
        
        return res
    
        
    def button_scrap(self): 
        res = super(MrpProduction, self).button_scrap()
        lista_de_productos = [self.product_id.product_tmpl_id.id]
        for prod_component in self.move_raw_ids.product_id.product_tmpl_id.ids:
                lista_de_productos.append(prod_component)

        if len(lista_de_productos)== 1:
                shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.product_id.product_tmpl_id.id)])
        else:
                shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','in',lista_de_productos)])

        for product in shopify_product_template: 
            process_import_export_obj = False
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : product.shopify_instance_id.id,
            })

            if process_import_export_obj: 
                process_import_export_obj.with_context({'active_ids' : [product.id]}).shopify_selective_product_stock_export()
        
        return res
    
    
    def button_unbuild(self): 
        res = super(MrpProduction, self).button_unbuild()

        lista_de_productos = [self.product_id.product_tmpl_id.id]
        for prod_component in self.move_raw_ids.product_id.product_tmpl_id.ids:
                lista_de_productos.append(prod_component)

        if len(lista_de_productos)== 1:
                shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.product_id.product_tmpl_id.id)])
        else:
                shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','in',lista_de_productos)])

        for product in shopify_product_template: 
            process_import_export_obj = False
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : product.shopify_instance_id.id,
            })

            if process_import_export_obj: 
                process_import_export_obj.with_context({'active_ids' : [product.id]}).with_delay(eta=2).shopify_selective_product_stock_export()
        

        return res