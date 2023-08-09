import requests
import threading
import base64

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from  ..multiversion.models.vex_soluciones_meli_config import API_URL, CATEGORIES_REQUIRED_ATRR , CATEGORIES_REQUIRED_BRAND
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime
import math
import time

from datetime import datetime, timedelta

id_api       = 'id_vex'
server_api   = 'server_vex'

class MeliActionSynchro(models.TransientModel):
    _inherit       = "vex.synchro"

    def json_fields(self, data, query, server, accion=None):
        res = super(MeliActionSynchro, self).json_fields(data, query, server)
        if server.conector == 'meli':

            create = {}
            write = {}
            if query == "products":
                # raise ValueError(str(data))
                if not 'body' in data:
                    import json
                    raise ValidationError('ka')
                    # raise ValidationError('no existe body in data')
                body = data['body']
                # raise ValidationError(str(body['attributes']))

                active = "'t'" if body['status'] == 'active' else "'f'"
                condicion = "'" + body['condition'] + "'" if body['condition'] else "' '"

                if not server.categ_id:
                    raise ValidationError('not indicate category product')

                # raise ValidationError(str(data))

                # if body['id'] == 'MLM1650434284':
                #    raise ValidationError(str(data))
                name = "'"+body['title']+"'"

                # description = description.replace('%', body['Description'])
                # description = description.replace('%', body['Description'])
                # description = description.replace('%', body['Description'])

                create = {
                    'conector': "'meli'",
                    'server_vex': server.id,
                    'id_vex': "'"+body['id']+"'",
                    'name': name,
                    # 'list_price': body['price'] if body['price'] else 0,
                    'type': "'product'",
                    'detailed_type': "'product'",
                    'categ_id': server.categ_id.id,
                    # 'is_published': active,
                    'product_condition': condicion,
                    'active_meli': active,
                    'permalink': "'{}'".format(body['permalink']),
                    'base_unit_count': 0,
                    'create_of_meli': "'t'"
                    # 'default_code': "'" + body['id'] + "'",
                    # 'public_categ_ids': [(6, 0, [self.check_categories(body['category_id'], server, None).id])]
                }
                write = {
                    # 'name': "'" + body['title'] + "'",
                    # 'list_price': body['price'],
                    # 'type': "'product'",
                    # 'detailed_type': "'product'",
                    # 'categ_id': server.categ_id.id,
                    'permalink': "'" + body['permalink'] + "'",
                    'product_condition': condicion,
                    'active_meli': active,
                    # 'default_code': "'" + body['id'] + "'",
                    # 'id_vex': "'" + body['id'] + "'",
                    # 'conector': "'meli'",
                }

                if 'attributes' in body:
                    for atributes in body['attributes']:
                        if atributes['id'] == 'SELLER_SKU':
                            create['default_code'] = f"'{atributes['value_name']}'"
                            # write['default_code'] = f"'{atributes['value_name']}'"
                # raise ValidationError(str(create))

            if query == "orders":
                # raise ValidationError(str(data))
                d = str(data['date_created']).split('.')

                fecha = datetime.strptime(d[0], '%Y-%m-%dT%H:%M:%S')
                # raise ValidationError(fecha)

                fecha = fecha + timedelta(hours=3)

                pricelist = server.pricelist
                if not pricelist:
                    raise ValidationError("Set Up pricelist")
                salesteam = server.sales_team
                if not salesteam:
                    raise ValidationError("Set Up Sales Team")
                if not server.warehouse:
                    raise ValidationError("Set Up Warehouse")
                dx = {'customer': {}, 'billing': {}}

                # id_customer = str(data['buyer']['id'])
                # url_customer = f'''https://api.mercadolibre.com/users/{id_customer}'''

                # item = requests.get(url_customer,params={'access_token': server.access_token}).json()

                # url_envio = f'''https://api.mercadolibre.com/shipments/{str(data['shipping']['id'])}'''

                # envio = requests.get(url_envio,params={'access_token': server.access_token}).json()

                # raise ValidationError(str(envio))

                # nam = "{}".format(str(data['buyer']['nickname']))
                nam = None
                if 'first_name' in data['buyer']:
                    nam = data['buyer']['first_name']

                if 'last_name' in data['buyer']:
                    nam += ' ' + data['buyer']['last_name']

                # raise ValueError(nam)

                if 'phone' in dx['customer']:
                    dx['customer']['phone'] = "'{}'".format(
                        str(data['buyer']['phone']['area_code']) + "-" + str(data['buyer']['phone']['number']))

                # consultar informacion de facturacion
                url_invoice = f'''https://api.mercadolibre.com/orders/{data['id']}/billing_info'''
                data_invoice = requests.get(url_invoice, params={'access_token': server.access_token})

                # raise ValidationError(str(data_invoice.json()))
                coorect_invoice = False



                if coorect_invoice and data_invoice.status_code == 200:
                    data_invoice = data_invoice.json()
                    coorect_invoice = True
                    dx['billing']['name'], dx['billing']['display_name'] = nam, nam
                    dx['billing']['street'] = ''
                    # raise ValueError(data_invoice)
                    if 'billing_info' in data_invoice:
                        if 'doc_number' in data_invoice['billing_info']:
                            dx['customer']['vat'] = f''' {data_invoice['billing_info']['doc_number']} '''
                        if 'additional_info' in data_invoice['billing_info']:
                            street = ''
                            STREET_NUMBER = ''
                            COMMENT = ''
                            CITY_NAME = ''
                            STATE_NAME = ''
                            COUNTRY_NAME = ''
                            first_name = ''
                            last_name = ''
                            pais = None
                            state = None
                            for dati in data_invoice['billing_info']['additional_info']:
                                if dati['type'] == 'BUSINESS_NAME':
                                    nx = f''' '{dati['value']}' '''
                                    dx['billing']['name'], dx['billing']['display_name'] = nx, nx
                                if dati['type'] == 'STREET_NAME':
                                    street = dati['value']
                                if dati['type'] == 'STREET_NUMBER':
                                    STREET_NUMBER = dati['value']
                                if dati['type'] == 'COMMENT':
                                    COMMENT = dati['value']
                                if dati['type'] == 'CITY_NAME':
                                    CITY_NAME = dati['value']

                                if dati['type'] == 'STATE_NAME':
                                    STATE_NAME = dati['value']
                                    if server.import_adress_in_fields:
                                        dmmx = [('name', '=', dati['value'])]
                                        state = self.env['res.country.state'].search(dmmx)
                                        # raise ValueError([state.display_name,dmmx])
                                        if state:
                                            state = state.id

                                if dati['type'] == 'FIRST_NAME':
                                    first_name = dati['value']
                                if dati['type'] == 'LAST_NAME':
                                    last_name = dati['value']

                                if dati['type'] == 'COUNTRY_ID':
                                    COUNTRY_NAME = dati['value']
                                    if server.import_adress_in_fields:
                                        dmmx = [('code', '=', dati['value'])]
                                        pais = self.env['res.country'].search(dmmx)
                                        if pais:
                                            pais = pais.id

                            if first_name != '' or last_name != '':
                                name_full = first_name + ' ' + last_name
                                dx['billing']['name'], dx['billing'][
                                    'display_name'] = f''' '{name_full}'  ''', f''' '{name_full}'  '''
                                # raise ValueError([name_full,dx])
                                if not nam:
                                    nam = name_full

                            if STREET_NUMBER != '':
                                street += ' ' + STREET_NUMBER

                            if COMMENT != '':
                                street += ' - ' + COMMENT
                            if server.import_adress_in_fields:
                                if pais:
                                    dx['billing']['country_id'] = pais
                                if state:
                                    dx['billing']['state_id'] = state
                                dx['billing']['city'] = f''' '{CITY_NAME}' '''
                            else:
                                if CITY_NAME != '':
                                    street += ' , ' + CITY_NAME
                                if COUNTRY_NAME != '':
                                    street += ' , ' + COUNTRY_NAME

                            if STATE_NAME != '':
                                street += ' , ' + STATE_NAME

                            street = street.replace("'", "")

                            dx['billing']['street'] = f''' '{street}' '''

                dx['customer']['name'], dx['customer']['display_name'] = nam, nam

                # raise ValueError(dx)
                customer = self.check_customer(dx, server, data['buyer']['id'], [data, data_invoice])
                del dx

                # raise ValueError([nam,customer['invoice'].display_name,customer['shipping'].display_name,customer['customer'].display_name])

                pack_id = data['pack_id']
                id_meli = data['id']
                if pack_id:
                    id_meli = pack_id
                    # seq = pack_id
                # raise ValueError(customer)
                if server.use_sequence_order:
                    sqx = server.sequence_id
                    if not sqx:
                        raise ValidationError('sequence not found in instance')
                    seq = self.env['ir.sequence'].next_by_code(sqx.code)
                else:
                    seq = str(id_meli)
                    if server.prefix_sequence:
                        seq = server.prefix_sequence + ' ' + seq

                # raise ValueError(fecha)

                create = {

                    'conector': "'meli'",
                    'server_vex': server.id,
                    'id_vex': "'" + str(id_meli) + "'",

                    'client_order_ref': "'" + str(id_meli) + "'",
                    'name': "'" + str(seq) + "'",
                    'partner_id': customer['customer'].id,
                    'partner_invoice_id': customer['invoice'].id,
                    'partner_shipping_id': customer['shipping'].id,
                    'pricelist_id': server.pricelist.id,
                    'date_order': "'" + str(fecha) + "'",
                    'date_vex_order': "'" + str(fecha) + "'",
                    'create_date': "'" + str(fecha.date()) + "'",
                    'amount_untaxed': float(data['total_amount']),
                    'amount_total': float(data['total_amount']),
                    'meli_status': "'" + str(data['status']) + "'",
                    'meli_shipping_id': "'" + str(data['shipping']['id']) + "'",
                    # 'team_id': salesteam.id,
                    # 'woo_date_created': "'"+str(data['date_created']) + "'",
                    # 'woo_payment_method': "'"+str(data['payment_method_title']) + "'",
                    'payment_term_id': server.payment_term.id,
                    'picking_policy': "'" + str(server.picking_policy) + "'",
                    'warehouse_id': server.warehouse.id,
                    'state': "'draft'",
                    'company_id': server.company.id,
                    'user_id': server.user_sale_id.id,

                }

                write = {
                    # 'state': "''".format(state),
                    # 'client_order_ref': "'" + str(id_meli) + "'",
                    # 'meli_status': "'" + str(data['status']) + "'",
                    # 'name': "'" + str(seq) + "'",

                    'date_order': "'" + str(fecha) + "'",
                }

                if pack_id:
                    create['meli_pack_id'] = "'" + str(pack_id) + "'"
                    write['meli_pack_id'] = "'" + str(pack_id) + "'"

                # raise ValidationError(str(write))
            if query == "categories":
                create = {
                    'conector': "'meli'",
                    # 'server_vex': server.id,
                    'name': "'" + data['name'] + "'",
                    'id_vex': "'" + data['id'] + "'",
                }
                if data['id'] in CATEGORIES_REQUIRED_ATRR:
                    create['required_manufacture_meli'] = "'t'"
                if data['id'] in CATEGORIES_REQUIRED_BRAND:
                    create['required_brand_meli'] = "'t'"
                write = create

            res['create'].update(create)
            res['write'].update(write)

        return res