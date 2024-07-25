# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopify_tag_ids = fields.Many2many("shopify.tags")
    product_collection_ids = fields.Many2many('shopify.product.collection', string="Collections")
    
    

    def write(self, vals):
        collecciones_antes = self.product_collection_ids
        res = super(ProductTemplate, self).write(vals)
        campos_price = ['additional_cost_ids', 'margin_ids', 'replacement_cost','variant_seller_ids', 'taxes_id']
        if any(clave in vals for clave in campos_price):
            process_import_export_obj = False
            lista_productos = [self.id]
            boms_with_product = self.env['mrp.bom'].search([('bom_line_ids.product_tmpl_id', '=', self.id)])
            for bom in boms_with_product:
                lista_productos.append(bom.product_id.product_tmpl_id.id)
            #ciclo de boms
            encontrados = True
            vuelta = 0
            contador  = 0  #poner un limite por el momento mientras se me ocurre una manera mejor
            while encontrados:
                contador = 0
                vuelta += 1
                boms_with_product = self.env['mrp.bom'].search([('bom_line_ids.product_tmpl_id', 'in', lista_productos)])
                for bom in boms_with_product:
                    if bom.product_id.product_tmpl_id.id not in lista_productos: 
                        lista_productos.append(bom.product_id.product_tmpl_id.id)
                        contador += 1
                if contador == 0:
                    encontrados = False
                if vuelta == 3:
                    encontrados = False
                #termina ciclo de boms



            if len(lista_productos)== 1:
                shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.id)])
            else:
                shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','in',lista_productos)])
            for product in shopify_product_template:
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
            
                if process_import_export_obj: 
                    process_import_export_obj.shopify_is_set_price = True
                    process_import_export_obj.with_context({'active_ids' : [product.id]}).sudo().manual_update_product_to_shopify()

        campos_datos = ['name', 'description', 'description_sale', 'shopify_tag_ids']
        if any(clave in vals for clave in campos_datos):
            process_import_export_obj = False
            shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.id)])
            for product in shopify_product_template:
                if 'name' in vals:
                    product.name = self.name
                    for variant in product.shopify_product_ids:
                        variant.name = self.name
                if 'description_sale' in vals:
                    product.description = self.description_sale
                    for variant in product.shopify_product_ids:
                        #variant.description = self.description_sale
                        pass
                if 'shopify_tag_ids' in vals:
                    product.tag_ids = self.shopify_tag_ids


                process_import_export_obj = self.env['shopify.process.import.export'].create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
                
                if process_import_export_obj: 
                    process_import_export_obj.shopify_is_update_basic_detail = True
                    process_import_export_obj.with_context({'active_ids' : [product.id]}).sudo().manual_update_product_to_shopify()

        campos_imagen = ['ept_image_ids', 'test']
        if any(clave in vals for clave in campos_imagen):
            process_import_export_obj = False
            shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.id)])
            for product in shopify_product_template:
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
                
                if process_import_export_obj: 
                    process_import_export_obj.shopify_is_set_image = True
                    process_import_export_obj.with_context({'active_ids' : [product.id]}).sudo().manual_update_product_to_shopify()
            
        campos_collection = ['product_collection_ids']
        if any(clave in vals for clave in campos_collection):
            collecciones_despues = self.product_collection_ids
            collecciones_eliminadas = list(set(collecciones_antes.ids) - set(collecciones_despues.ids))
            collecciones_agregadas = list(set(collecciones_despues.ids) - set(collecciones_antes.ids))
            if len(collecciones_eliminadas) == 1:
                shopify_colleciones_eliminadas = self.env['shopify.product.collection'].search([('id','=',collecciones_eliminadas)])                                                        
            if len(collecciones_eliminadas) > 1:
                shopify_colleciones_eliminadas = self.env['shopify.product.collection'].search([('id','in',collecciones_eliminadas)])
            if len(collecciones_agregadas) == 1:
                shopify_collecciones_agregadas = self.env['shopify.product.collection'].search([('id','=',collecciones_agregadas)])
            if len(collecciones_agregadas) > 1:
                shopify_collecciones_agregadas = self.env['shopify.product.collection'].search([('id','in',collecciones_agregadas)])
            if len(collecciones_agregadas) > 0:  
                for colleccion in shopify_collecciones_agregadas:
                    colleccion.shopify_instance_id.connect_in_shopify()
                    collect = colleccion.request_collection(colleccion.shopify_collection_id)
                    shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.id)])
                    new_product = colleccion.request_product(shopify_product_template.shopify_tmpl_id)
                    collect.add_product(new_product)
            if len(collecciones_eliminadas) > 0:  
                for colleccion in shopify_colleciones_eliminadas:
                    colleccion.shopify_instance_id.connect_in_shopify()
                    collect = colleccion.request_collection(colleccion.shopify_collection_id)
                    shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.id)])
                    new_product = colleccion.request_product(shopify_product_template.shopify_tmpl_id)
                    collect.remove_product(new_product)




        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        campos_actualizacion_shoppify = ['weight', 'test']
        if any(clave in vals for clave in campos_actualizacion_shoppify):
            process_import_export_obj = False
            shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.product_tmpl_id.id)])
            for product in shopify_product_template:
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
                
                if process_import_export_obj: 
                    process_import_export_obj.shopify_is_update_basic_detail = True
                    process_import_export_obj.with_context({'active_ids' : [product.id]}).sudo().manual_update_product_to_shopify()
            
        return res