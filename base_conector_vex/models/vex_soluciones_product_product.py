from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'
    id_vex_varition = fields.Char(string="ID Variation")
    vex_regular_price = fields.Float()
    stock_vex = fields.Float()
    log_meli_txt = fields.Text()

    _sql_constraints = [
        ('uni_id_variante_prro_vex', 'unique(product_tmpl_id,server_vex)',
         'There can be no duplication of synchronized products Variations')
    ]

    def del_id_connector_vex(self):
        self.id_vex_varition = False
        if len(self.product_tmpl_id.product_variant_ids) == 1:
            self.product_tmpl_id.id_vex = False
            self.product_tmpl_id.conector = False
            self.product_tmpl_id.server_vex = False

    @api.depends('list_price', 'price_extra')
    def _compute_product_lst_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse([self._context['uom']])
        for product in self:
            if to_uom:
                list_price = product.uom_id._compute_price(product.list_price, to_uom)
            else:
                list_price = product.list_price
            api_precio = product.vex_regular_price
            if api_precio:
                product.lst_price = api_precio
            else:
                product.lst_price = list_price + product.price_extra

    def update_conector_vex(self):
        return

    def _get_display_price_meli(self, product,pricelist_id,datex,server_vex,qty):
        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price

        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.

        #no_variant_attributes_price_extra = [
        #    ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
        #        lambda ptav:
        #        ptav.price_extra and
        #        ptav not in product.product_template_attribute_value_ids
        #    )
        #]
        #if no_variant_attributes_price_extra:
        #    product = product.with_context(
        #        no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
        #    )


        if pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=pricelist_id.id, uom=product.uom_id.id).price
        product_context = dict(
            self.env.context,
            #partner_id=self.order_id.partner_id.id,
            date=datex,
            uom=product.uom_id.id
        )

        final_price, rule_id = pricelist_id.with_context(product_context).get_product_price_rule(
            product , qty or 1.0, self.env.company.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                           qty,
                                                                                           product.uom_id.id,
                                                                                           pricelist_id.id)
        if currency != pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, pricelist_id.currency_id,
                server_vex.company or self.env.company, datex or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

