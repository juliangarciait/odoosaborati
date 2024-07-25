from ...shopify_ept import shopify
from ...shopify_ept.shopify.pyactiveresource.connection import ClientError

_logger = logging.getLogger("SHOPIFY OPERATIONS")

def manual_export_product_to_shopify(self):
        """ This method is used to call child method for export products from shopify layer products to Shopify store.
            It calls from the Shopify layer product screen.
        """
        start = time.time()
        shopify_product_template_obj = self.env["shopify.product.template.ept"]
        shopify_product_obj = self.env['shopify.product.product.ept']
        instance_obj = self.env['shopify.instance.ept']
        shopify_products = self._context.get('active_ids', [])
        template = shopify_product_template_obj.browse(shopify_products)
        templates = template.filtered(lambda x: not x.exported_in_shopify)
        if templates and len(templates) > 80:
            raise UserError(_("Error:\n- System will not export more then 80 Products at a "
                              "time.\n- Please select only 80 product for export."))
        shopify_instances = instance_obj.search([])
        for instance in shopify_instances:
            shopify_templates = templates.filtered(lambda product: product.shopify_instance_id == instance)
            if shopify_templates:
                shopify_product_obj.with_delay(eta=5).shopify_export_products(instance,
                                                            self.shopify_is_set_basic_detail,
                                                            self.shopify_is_set_price,
                                                            self.shopify_is_set_image,
                                                            self.shopify_is_publish,
                                                            shopify_templates)
        self.with_delay(eta=5).export_stock(shopify_products)
        end = time.time()
        _logger.info("Export Processed %s Products in %s seconds.", str(len(templates)), str(end - start))
        return True

def export_stock(self, ids): 
        self.with_context({'active_ids': ids}).shopify_selective_product_stock_export()

