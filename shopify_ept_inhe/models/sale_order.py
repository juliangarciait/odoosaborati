from odoo import models, fields, api, _
from odoo.tools.misc import get_lang
import logging 
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model): 
    _inherit = 'sale.order'

    def action_confirm(self): 
        res = super(SaleOrder, self).action_confirm()

        lista_productos = []
        for line in self.order_line:
            lista_productos.append(line.product_template_id.id)

        if len(lista_productos) == 1:
            boms_with_product = self.env['mrp.bom'].search([('bom_line_ids.product_tmpl_id', '=', lista_productos)])
        else: 
            boms_with_product = self.env['mrp.bom'].search([('bom_line_ids.product_tmpl_id', 'in', lista_productos)])
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
            
        if len(lista_productos)== 1:
            shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.id)])
        else:
            shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','in',lista_productos)])
        for product in shopify_product_template:
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
            if process_import_export_obj: 
                process_import_export_obj.with_context({'active_ids' : [product.id]}).shopify_selective_product_stock_export()

        
        return res

    def action_cancel(self): 
        res = super(SaleOrder, self).action_cancel()
        lista_productos = []
        for line in self.order_line:
            lista_productos.append(line.product_template_id.id)

        if len(lista_productos) == 1:
            boms_with_product = self.env['mrp.bom'].search([('bom_line_ids.product_tmpl_id', '=', lista_productos)])
        else: 
            boms_with_product = self.env['mrp.bom'].search([('bom_line_ids.product_tmpl_id', 'in', lista_productos)])
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
            
        if len(lista_productos)== 1:
            shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','=',self.id)])
        else:
            shopify_product_template = self.env['shopify.product.template.ept'].search([('product_tmpl_id','in',lista_productos)])
        for product in shopify_product_template:
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                 'shopify_instance_id' : product.shopify_instance_id.id,
             })
            if process_import_export_obj: 
                process_import_export_obj.with_context({'active_ids' : [product.id]}).shopify_selective_product_stock_export()

        return res