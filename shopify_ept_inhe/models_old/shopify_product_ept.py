import json
import logging
import time
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from ...shopify_ept import shopify
from ...shopify_ept.shopify.pyactiveresource.connection import ClientError
from ...shopify_ept.shopify.pyactiveresource.connection import ResourceNotFound

_logger = logging.getLogger("Shopify Product")


class ShopifyProductProductEpt(models.Model):
    _inherit = "shopify.product.product.ept"

    product_status = fields.Selection([('draft', 'Draft'), ('active', 'Active')], default="draft", string="Product status")
    to_shopify = fields.Boolean(default=True)

    def prepare_shopify_product_for_update_export(self, new_product, template, instance, is_set_basic_detail,
                                                  is_publish, is_set_price):
        if is_set_basic_detail or is_publish:
            self.shopify_set_template_value_in_shopify_obj(new_product, template, is_publish, is_set_basic_detail)
        if is_set_basic_detail or is_set_price:
            variants = []
            for variant in template.shopify_product_ids:
               variant_vals = self.shopify_prepare_variant_vals(instance, template, variant, is_set_price,
                                                            is_set_basic_detail)
               if variant_vals.get('price') != None and instance.shopify_company_id.id == 2: 
                    if variant_vals.get('price') > 5.00: 
                        variants.append(variant_vals)
                        product_in_log_exist = self.env['product.log'].search([('product_id', '=', variant.product_id.id), ('instance_id', '=', instance.id)])
                        if product_in_log_exist: 
                            product_in_log_exist.unlink()
                    else: 
                        product_in_log_exist = self.env['product.log'].search([('product_id', '=', variant.product_id.id), ('instance_id', '=', instance.id)])
                        if not product_in_log_exist: 
                            create_product_in_log = self.env['product.log'].create(
                                {
                                    'product_id' : variant.product_id.id, 
                                    'instance_id': instance.id
                                }
                            )
               else: 
                    _logger.info('()'*100)
                    _logger.info(variant_vals)
                    variants.append(variant_vals)
            new_product.variants = variants
        if is_set_basic_detail:
            self.prepare_export_update_product_attribute_vals(template, new_product)
        return True
    
    def shopify_export_products(self, instance, is_set_basic_detail, is_set_price, is_set_images, is_publish,
                                templates):
        """
        This method used to Export the shopify product from Odoo to Shopify.
        :param instance:Record of the instance
        :param is_set_basic_detail: It exports the product basic details if it is True.
        :param is_set_price: If true it is the export price with the product else not the export price with the product.
        :param is_set_images: If true it is the export images with the product else not the export images with the
        product.
        :param is_publish: If true it publishes the product in the Shopify store.
        @author: Nilesh Parmar @Emipro Technologies Pvt. Ltd on date 19/11/2019.
        """
        common_log_obj = self.env["common.log.book.ept"]
        common_log_line_obj = self.env["common.log.lines.ept"]
        model = "shopify.product.product.ept"
        model_id = common_log_line_obj.get_model_id(model)
        instance.connect_in_shopify()
        log_book_id = common_log_obj.shopify_create_common_log_book("export", instance, model_id)

        for template in templates:
            new_product = shopify.Product()

            self.prepare_shopify_product_for_update_export(new_product, template, instance, is_set_basic_detail,
                                                           is_publish, is_set_price)

            result = new_product.save()

            if not result:
                message = "Product %s not exported in Shopify Store." % template.name
                self.shopify_export_product_log_line(message, model_id, log_book_id)
            if result:
                self.update_products_details_shopify_third_layer(new_product, template, is_publish)
            if new_product and is_set_images:
                self.export_product_images(instance, shopify_template=template)
            if new_product and template.product_tmpl_id.product_collection_ids: 
                self.export_collections(template.product_tmpl_id.product_collection_ids, new_product, template)
            self._cr.commit()

        if not log_book_id.log_lines:
            log_book_id.unlink()
        return True
    
    def export_collections(self, collections, shopify_product, template): 
        for product_collection in collections:
            product_collection.shopify_instance_id.connect_in_shopify()     
            if product_collection.is_exported and product_collection.company_id.id == self.env.company.id and product_collection.shopify_instance_id == template.shopify_instance_id:
                self.add_product(product_collection, shopify_product)


    def add_product(self, product_collection, shopify_product): 
        collect = product_collection.request_collection(product_collection.shopify_collection_id)
        if collect:
            shopify_product.add_to_collection(collect)


    def shopify_set_template_value_in_shopify_obj(self, new_product, template, is_publish, is_set_basic_detail):
        published_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        if is_publish == "unpublish_product":
            new_product.published_at = None
            new_product.published_scope = "null"
        elif is_publish == "publish_product_global":
            new_product.published_scope = "global"
            new_product.published_at = published_at
        else:
            new_product.published_scope = "web"
            new_product.published_at = published_at

        instance = template.shopify_instance_id
        if is_set_basic_detail:
            new_product.body_html = template.description if template.description else '' 
            new_product.vendor = template.brand.name if template.brand.name else ''
            new_product.status = template.product_status
            new_product.product_type = template.shopify_product_category.name if template.shopify_product_category.name else ''
            new_product.tags = [tag.name for tag in template.tag_ids] if template.tag_ids else []

            if template.template_suffix:
                new_product.template_suffix = template.template_suffix
            # new_product.title = template.name
            new_product.title = template.with_context(lang=instance.shopify_lang_id.code).name

        return True

    def shopify_prepare_variant_vals(self, instance, template, variant, is_set_price, is_set_basic_detail):
        """This method used to prepare variant vals for export product variant from
            shopify third layer to shopify store.
            :param variant: Record of shopify product product(shopify product variant)
            @return: variant_vals
            @author: Nilesh Parmar @Emipro Technologies Pvt. Ltd on date 15/11/2019.
        """
        variant_vals = {}
        if variant.variant_id:
            variant_vals.update({"id": variant.variant_id})
        if is_set_price:
            variant.with_company(instance.shopify_company_id.id).product_id.read(['lst_price', 'name', 'id'])
            price = instance.shopify_pricelist_id.with_company(instance.shopify_company_id.id).get_product_price(variant.product_id, 1.0, partner=False,
                                                                    uom_id=variant.product_id.uom_id.id)
            
            if float(price) > 0.0:
                if template.with_company(instance.shopify_company_id.id).product_tmpl_id.taxes_id.company_id.id == instance.shopify_company_id.id: 
                    total = template.product_tmpl_id.taxes_id.compute_all(float(price), product=template.product_tmpl_id, partner=self.env['res.partner'])
                    variant_vals.update({"price": float(total['total_included'])})
                else: 
                    variant_vals.update({"price": float(price)})
            elif float(price) == 0.0 and template.product_tmpl_id.list_price > 0.0:
                if template.with_company(instance.shopify_company_id.id).product_tmpl_id.taxes_id.company_id.id == instance.shopify_company_id.id: 
                    total = template.product_tmpl_id.taxes_id.compute_all(float(template.product_tmpl_id.list_price), product=template.product_tmpl_id, partner=self.env['res.partner'])
                    variant_vals.update({"price": float(total['total_included'])})
                else:
                    variant_vals.update({"price": float(price)})
            else: 
                raise ValidationError("El producto no se puede mandar a shopify porque su precio (en la lista de precio seleccionada) es de 0")
            variant_vals.update({'cost': variant.product_id.replacement_cost, 'collections': 1})

        if is_set_basic_detail:
            variant_vals = self.prepare_vals_for_product_basic_details(variant_vals, variant, instance)

        if variant.inventory_management == "shopify":
            variant_vals.update({"inventory_management": "shopify"})
        else:
            variant_vals.update({"inventory_management": None})

        if variant.check_product_stock == "continue":
            variant_vals.update({"inventory_policy": "continue"})
        else:
            variant_vals.update({"inventory_policy": "deny"})

        return variant_vals 
    
    def request_for_shopify_product_variant(self, shopify_variant_id):
        shopify_variant = False
        try:
            shopify_variant = shopify.Product().find(variant_id=shopify_variant_id)
        except ClientError as error:
            if hasattr(error, "response") and error.response.code == 429 and error.response.msg == "Too Many Requests":
                time.sleep(int(float(error.response.headers.get('Retry-After', 5))))
                shopify_variant = shopify.Product().find(variant_id=shopify_variant_id)

        return shopify_variant
    
    def update_product_images(self, shopify_template):
        """
        This method is used for the update Shopify product images if image is new in product then export image in
        shopify store.
        :param shopify_template: use for the shopify template.
        Author:Bhavesh Jadav 18/12/2019
        """
        if not shopify_template.shopify_image_ids:
            return False
        shopify_images = self.request_for_shopify_product_images(shopify_template)
        for shop_image in shopify_images:
            shop_image.destroy()
        position = 0
        for image in shopify_template.shopify_image_ids:
            if image.odoo_image_id.image:
                position += 1
                shopify_image = shopify.Image()
                shopify_image.product_id = shopify_template.shopify_tmpl_id
                shopify_image.attachment = image.odoo_image_id.image.decode("utf-8")
                shopify_image.position = position
                #exists_variant = False
                if image.shopify_variant_id:
                    shopify_image.variant_ids = [int(image.shopify_variant_id.variant_id)]
                    #exists_variant = self.request_for_shopify_product_variant(image.shopify_variant_id.variant_id)
                #if not exists_variant:
                    #shopify_image.save()
                result = shopify_image.save()
                #else:
                    #shopify_image = exists_variant[0]
                if result:    
                    image.write({"shopify_image_id": shopify_image.id})
                time.sleep(2)
        return True
    

    @api.model
    def export_stock_in_shopify(self, instance, product_ids):
        common_log_line_obj = self.env["common.log.lines.ept"]
        product_obj = self.env["product.product"]
        sale_order_obj = self.env["sale.order"]
        log_line_array = []
        model = "shopify.product.product.ept"
        model_id = common_log_line_obj.get_model_id(model)
        all_products = self.search_shopify_product_for_export_stock(instance, product_ids)

        if self._context.get('is_process_from_selected_product'):
            shopify_products = all_products
        else:
            if instance.shopify_last_date_update_stock:
                shopify_products = all_products.filtered(lambda x: not x.last_stock_update_date or
                                                                   x.last_stock_update_date <= instance.shopify_last_date_update_stock)
            else:
                shopify_products = all_products.filtered(lambda x: not x.last_stock_update_date)

        if not shopify_products:
            return False
        last_export_date = all_products[0].last_stock_update_date or datetime.now()

        if not shopify_products:
            return True

        instance.connect_in_shopify()
        location_ids = self.env["shopify.location.ept"].search(
            [("instance_id", "=", instance.id), ('legacy', '=', False)])
        if not location_ids:
            message = "Location not found for instance %s while update stock" % instance.name
            log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)

        shopify_templates = self.check_available_products_in_shopify(instance)
        if shopify_templates:
            shopify_template_ids = shopify_products.mapped('shopify_template_id')
            shopify_products = shopify_template_ids.filtered(
                lambda template: template.id in shopify_templates.ids).shopify_product_ids

        for location_id in location_ids:
            shopify_location_warehouse = location_id.export_stock_warehouse_ids or False
            if not shopify_location_warehouse:
                message = "No Warehouse found for Export Stock in Shopify Location: %s" % location_id.name
                log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)
                continue

            odoo_product_ids = shopify_products.product_id.ids
            product_stock = self.sudo().check_stock(instance, odoo_product_ids, product_obj,
                                             location_id.export_stock_warehouse_ids)
            commit_count = 0
            for shopify_product in shopify_products:
                if commit_count == 50:
                    self._cr.commit()
                    commit_count = 0
                commit_count += 1
                odoo_product = shopify_product.product_id
                if odoo_product.detailed_type == "product":
                    if not shopify_product.inventory_item_id:
                        message = "Inventory Item Id did not found for Shopify Product Variant ID " \
                                  "%s with name %s for instance %s while Export stock" % (
                                      shopify_product.id, shopify_product.name, instance.name)
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)
                        continue

                    quantity = self.compute_qty_for_export_stock(product_stock, shopify_product, odoo_product)
                    try:
                        shopify.InventoryLevel.set(location_id.shopify_location_id, shopify_product.inventory_item_id,
                                                   int(quantity))
                    except ClientError as error:
                        if hasattr(error,
                                   "response") and error.response.code == 429 and error.response.msg == "Too Many Requests":
                            time.sleep(int(float(error.response.headers.get('Retry-After', 5))))
                            shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                       shopify_product.inventory_item_id,
                                                       int(quantity))
                            continue
                        elif error.response.code == 422 and error.response.msg == "Unprocessable Entity":
                            if json.loads(error.response.body.decode()).get("errors")[
                                0] == 'Inventory item does not have inventory tracking enabled':
                                shopify_product.write({'inventory_management': "Dont track Inventory"})
                            continue
                        message = "Error while Export stock for Product ID: %s & Product Name: '%s' for instance:" \
                                  "'%s'\nError: %s\n%s" % (odoo_product.id, odoo_product.name, instance.name,
                                                           str(error.response.code) + " " + error.response.msg,
                                                           json.loads(error.response.body.decode()).get("errors")[0]
                                                           )
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)
                    except ResourceNotFound as error:
                        if hasattr(error, "response"):
                            message = "Error while Export stock for Product ID: %s & Product Name: '%s' for instance:" \
                                      "'%s'not found in Shopify store\nError: %s\n%s" % (
                                          odoo_product.id, odoo_product.name, instance.name,
                                          str(error.response.code) + " " + error.response.msg,
                                          json.loads(error.response.body.decode()).get("errors")[0]
                                      )
                            log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)
                    except Exception as error:
                        message = "Error while Export stock for Product ID: %s & Product Name: '%s' for instance: " \
                                  "'%s'\nError: %s" % (odoo_product.id, odoo_product.name, instance.name, str(error))
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)

                    if not self._context.get('is_process_from_selected_product'):
                        shopify_product.write({
                            'last_stock_update_date': last_export_date if not shopify_product.last_stock_update_date else datetime.now()})
        log_book_id = False
        if len(log_line_array) > 0:
            log_book_id = self.create_log_book(log_line_array, "export", instance)

        if log_book_id and instance.is_shopify_create_schedule:
            message = []
            count = 0
            for log_line in log_book_id.log_lines:
                count += 1
                if count <= 5:
                    message.append('<' + 'li' + '>' + log_line.message + '<' + '/' + 'li' + '>')
            if count >= 5:
                message.append(
                    '<' + 'p' + '>' + 'Please refer the logbook' + '  ' + log_book_id.name + '  ' + 'check it in more detail' + '<' + '/' + 'p' + '>')
            note = "\n".join(message)

            sale_order_obj.create_schedule_activity_against_logbook(log_book_id, log_book_id.log_lines, note)
        return all_products
    
    def check_stock(self, instance, product_ids, prod_obj, warehouse):
        product_stock = {}
        instance = instance.sudo()
        if product_ids:
            if instance.shopify_stock_field.name == "free_qty":
                product_stock = prod_obj.get_free_qty_ept(warehouse, product_ids)

            elif instance.shopify_stock_field.name == "virtual_available":
                product_stock = prod_obj.get_forecasted_qty_ept(warehouse, product_ids)

        return product_stock
    
    