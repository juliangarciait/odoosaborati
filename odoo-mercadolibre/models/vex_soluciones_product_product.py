from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
import requests
from .vex_soluciones_meli_config import CONDITIONS

class ProductProduct(models.Model):
    _inherit = 'product.product'
    product_condition = fields.Selection(CONDITIONS, string='Product Condition', help='Default product condition')
    brand = fields.Char(string="Product Brand")
    #questions_count = fields.Integer(required=False, compute='_count_questions')
    #questions = fields.One2many('meli.questions', 'product_id')
    active_meli = fields.Boolean(default=True)
    buying_mode = fields.Selection([('buy_it_now', 'buy it now'), ('classified', 'classified')])
    listing_type_id = fields.Selection([('free', 'free'), ('bronze', 'bronze'),
                                        ('gold_special', 'gold special')])
    name_product_meli = fields.Char(string="Titulo")


    def update_conector_vex(self):
        name = self.name_product_meli or self.name
        categ = self.public_categ_ids[0] if self.public_categ_ids else None
        if categ:
            if not categ.id_vex:
                categ = False
            else:
                categ = categ.id_vex
        if  self.id_vex_varition or self.id_vex :
            #id_vex =  self.id_vex_varition or self.id_vex



            return {
                'name': ('Update to ML'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'meli.export.unite',
                'target': 'new',
                # 'res_id': wiz.id,
                'context': {
                    'default_product': self.id,
                    #'default_brand': self.brand ,
                    'default_quantity': self.qty_available ,
                    'default_condition': self.product_condition,
                    'default_buying_mode': self.buying_mode ,
                    'default_listing_type_id': self.listing_type_id,
                    'default_name_product_meli': name ,
                    'default_category': categ

                }
            }
        else:
            if not self.image_1920:
                raise ValidationError('THIS PRODUCT DONT HAVE IMAGE')

            return {
                'name': ('Export to ML'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'meli.export.unite',
                'target': 'new',
                # 'res_id': wiz.id,
                'context': {
                    'default_product': self.id,
                    #'default_brand': self.brand ,
                    'default_quantity': self.qty_available ,
                    'default_condition': self.product_condition,
                    'default_buying_mode': self.buying_mode,
                    'default_listing_type_id': self.listing_type_id,
                    'default_name_product_meli': name,
                    'default_category': categ
                }
            }

