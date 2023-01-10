from odoo import api, fields, models
import threading
import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from odoo.addons.payment.models.payment_acquirer import ValidationError
from ..sdk.meli.configuration import  Configuration
from ..sdk.meli.api_client import ApiClient
from ..sdk.meli.api import RestClientApi
import base64
from ..models.vex_soluciones_meli_config import API_URL , CATEGORIES_REQUIRED_ATRR , CATEGORIES_REQUIRED_BRAND
from ..models.vex_soluciones_meli_config import CONDITIONS

class MeliMultiExport(models.TransientModel):
    _name = "meli.export"
    server = fields.Many2one('meli.synchro.instance',
                             "Instance", required=True)
    action = fields.Many2one('vex.restapi.list')
    model = fields.Char(related="action.model")
    products = fields.Many2many('product.template')

    def export_product(self,p,server,self2):
        if not p.default_code:
            raise ValidationError('ESTE PRODUCTO NO TIENE UN CODIGO DE REFERENCIA')
        if not p.image_1920:
            raise ValidationError('THIS PRODUCT DONT HAVE IMAGE')
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        foto_main = base_url+"/web/image?model=product.product&id={}&field=image_128&unique=".format(p.id)

        #raise   ValidationError(foto_main)

        headers = { "Content-Type": "application/json"}
        #url = self.env['shop.action.synchro'].shop_url(self.server, str(argument))
        price = float(p.list_price)
        if server.pricelist:
            price = p._get_display_price_meli(p,server.pricelist,fields.Date.today(),server,1)
        if p.id_vex or p.id_vex_varition:
            id_vex = p.id_vex_varition or p.id_vex
            url = f'https://api.mercadolibre.com/items/{id_vex}?access_token=' + str(server.access_token)
            data = {
                "price": price,
                "available_quantity": int(self2.quantity),

            }
            data['attributes'] = [
                #{
                #    "id": "MANUFACTURER",
                #    "value_name": f"{server.display_name}",
                #},
                {
                    'id': 'SELLER_SKU',
                    "value_name": p.default_code

                }
            ]
            r = requests.put(url, json=data, headers=headers)
            datax = r.json()
            p.log_meli_txt = str(data)+'\n'+str(datax)
        else:
            url = 'https://api.mercadolibre.com/items?access_token=' + str(server.access_token)
            if not self2.category_children:
                raise ValidationError('no seleciono una categoria')
            cc = self2.category_children if self2.category_children else self2.category
            # raise ValidationError(cc.id_app)
            if not self2.buying_mode:
                raise ValidationError('no selecciono un buying_mode')

            if not self2.listing_type_id:
                raise ValidationError('no selecciono un listing_type_id')

            if not self2.condition:
                raise ValidationError('no selecciono un condition')

            data = {
                "site_id": str(server.meli_country),
                "title": str(p.name),
                "category_id": str(cc.id_vex),
                # "category_id": str(cc.id_app),
                "price": price,
                "currency_id": str(server.default_currency),
                "buying_mode": str(self2.buying_mode),
                "listing_type_id": str(self2.listing_type_id),
                "condition": str(self2.condition),
                "available_quantity": int(self2.quantity),
                "pictures": [
                    {"source": foto_main}
                ],
            }

            atributes = []
            atributes.append({
                        'id': 'SELLER_SKU',
                        "value_name": p.default_code

                    })

            if cc.id_vex in CATEGORIES_REQUIRED_ATRR or cc.required_manufacture_meli == True:
                atributes.append({
                        "id": "MANUFACTURER",
                        "value_name": f"{server.display_name}",
                    })


            if cc.id_vex in CATEGORIES_REQUIRED_BRAND or cc.required_brand_meli == True:
                atributes.append({
                    "id": "BRAND",
                    "value_name": f"{server.display_name}",
                })


            data['attributes'] = atributes

            r = requests.post(url, json=data, headers=headers)


            datax = r.json()
            if 'id' in datax:
                # return
                # assig server
                # p.product_tmpl_id.server = server.id
                p.product_tmpl_id.conector = 'meli'
                p.product_tmpl_id.public_categ_ids = False
                p.product_tmpl_id.public_categ_ids = [(6 ,0 , [cc.id] )]
                #p.log_meli_txt = str(data)
                if len(p.product_tmpl_id.product_variant_ids) == 1:
                    p.product_tmpl_id.id_vex = str(datax['id'])

                p.id_vex_varition = str(datax['id'])
                p.product_condition = datax['condition']
                p.buying_mode = datax['buying_mode']
                p.listing_type_id = datax['listing_type_id']

            #else:
            #    import json
            #    raise ValidationError(json.dumps(data))
            #    # raise ValidationError('AN ERROR HAS OCCURRED, TRY AGAIN')

            p.log_meli_txt = str(data) + '\n' + str(datax)



    def export_export(self):
        threaded_synchronization = threading.Thread(target=self.start_export())
        threaded_synchronization.run()


    def start_export(self):
        model = self.model
        access_token = self.server.access_token
        if 1  == 1:
            if model == 'product.template':
                products = self.products
                for product in products:
                    self.export_product(product,self.server,self.category)

class MeliUnitExport(models.TransientModel):
    _name              = "meli.export.unite"
    server             = fields.Many2one('vex.instance',"Instancia", required=True)
    product            = fields.Many2one('product.product',required=True,string="Producto")
    id_vex             = fields.Char(related='product.id_vex')
    id_vex_varition    = fields.Char(related='product.id_vex_varition')
    category           = fields.Many2one('product.public.category',string="Categoria")
    category_children  = fields.Many2one('product.public.category',string="Sub Categoria")
    brand              = fields.Char()
    condition          = fields.Selection(CONDITIONS, string='Condición del producto')
    quantity           = fields.Integer(required=True,default=10,string="Stock")
    buying_mode        = fields.Selection([('buy_it_now','Compre ya'),('classified','clasificado')],string="Modo de Compra")
    listing_type_id    = fields.Selection([('free','gratis'),('bronze','Clásica'),('gold_special','Premium')],
                                          string="Tipo de Publicacion")

    #p.id_vex or p.id_vex_varition
    def start_export(self):
        self.env['vex.synchro'].check_synchronize(self.server)
        self.env['meli.export'].export_product(self.product,self.server,self)

    def predict_category(self):
        predict_url = '{}/sites/{}/category_predictor/predict'.format(API_URL, self.server.meli_country)
        payload = {'title': self.product.name}
        res = requests.get(predict_url, params=payload)
        #raise ValidationError(str([res,predict_url,payload]))
        if res.status_code == 200:
            res = res.json()
            cat_id = res['id']
            #raise ValidationError(cat_id)
            cc = self.env['product.public.category'].search([('id_app','=',cat_id)])
            if cc:
                self.category_children=cc.id
                self.category=cc.id

    @api.onchange('server')
    def change_server(self):
        if self.server.warehouse_stock_vex and self.product:
            quant = self.env['stock.quant'].search([('product_id','=',self.product.id),('on_hand','=',True),
                                            ('location_id','=',self.server.warehouse_stock_vex.lot_stock_id.id)])
            stock = 0
            if quant:
                stock = quant.quantity
            self.quantity = stock

    #def check_category(self):
    #    if self.server:
    #        #self.env['meli.action.synchro'].check_synchronize(self.server)
    #        self.predict_category()

    @api.onchange('category_children')
    def set_category_padre(self):
        self.category = self.category_children
    @api.onchange('category')
    def set_childrens(self):
        self.env['vex.synchro'].insert_categorias_children_meli(str(self.category.id_vex),self.server,self.category)
















