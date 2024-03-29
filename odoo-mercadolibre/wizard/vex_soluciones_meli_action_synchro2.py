import requests
import threading
import base64
from ..models.vex_soluciones_meli_config  import API_URL, INFO_URL, get_token
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..models.vex_soluciones_meli_config  import API_URL, CATEGORIES_REQUIRED_ATRR , CATEGORIES_REQUIRED_BRAND
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
    def get_data_id(self,id_vex,server,query):
        res = super(MeliActionSynchro, self).get_data_id(id_vex,server,query)
        if server.conector == 'meli':
            #raise ValidationError('h')
            if query == "products":
                item_url = '{}/items?ids={}&access_token={}'.format(API_URL, id_vex, server.access_token)
                #raise ValidationError(item_url)
                item = requests.get(item_url).json()
                return item[0]
            if query == "orders":
                #item_url = '{}/orders/{}&access_token={}'.format(API_URL, id_vex, server.access_token)
                url = 'https://api.mercadolibre.com/orders/{}'.format(id_vex)


                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + str(server.access_token)
                }
                res = requests.get(url, headers=headers)

                try:
                    res = res.json()
                except:
                    raise ValueError([res,url])




                return res

            if query == "categories":
                return self.get_category(id_vex)
                #raise ValidationError(str(res))
            #raise ValidationError(str(item))
            
        #raise ValueError([server,query])

        return res

    def insert_import_lines(self, server,accion,products_url,res):
        lines_wait = self.env['vexlines.import'].search([('accion', '=', accion.id),
                                                         ('instance','=',server.id)], limit=1)
        #raise ValidationError(lines_wait)
        if not lines_wait:
            #EJEUTA LA PRIMERA VES
            last = 0
            arg = ",".join(res['results'])


            self.json_execute_create('vexlines.import', {
                'url':  "'"+str(arg)+"'",
                'orden': last,
                'instance': server.id,
                'state': "'done'",
                'accion':accion.id
            })
            scroll_id = res['scroll_id']

            products_url = '{}/users/{}/items/search?search_type=scan&scroll_id={}&access_token={}'.format(API_URL,
                                                                                              str(server.user_id),scroll_id,
                                                                                              str(server.access_token))
            #raise ValidationError(products_url)
            res = requests.get(products_url).json()
            #import json
            #raise ValidationError(json.dumps(res))
            if res['results']:
                self.insert_import_lines(server,accion,products_url,res)

        else:
            last = self.env['vexlines.import'].search([('accion', '=', accion.id), ('instance', '=', server.id),
                                                       ('state', '=', 'done')], limit=1)
            last = int(last.orden) + 1
            arg = ",".join(res['results'])
            self.json_execute_create('vexlines.import', {
                'url': "'" + str(arg) + "'",
                'orden': last,
                'instance': server.id,
                'state': "'wait'",
                'accion': accion.id
            })
            scroll_id = res['scroll_id']
            products_url = '{}/users/{}/items/search?search_type=scan&scroll_id={}&access_token={}'.format(API_URL,
                                                                                                           str(server.user_id),
                                                                                                           scroll_id,

                                                                                              str(server.access_token))

            res = requests.get(products_url).json()
            if res['results']:
                self.insert_import_lines(server,accion,products_url,res)
            else:
                return 0
                raise ValueError(res)
                #raise ValidationError('oshee')
                #activar el cron
                update_cron = "UPDATE ir_cron SET accion={} , server_vex={}  WHERE argument = 'vex_cron' ".format(accion.id,server.id)
                self.env.cr.execute(update_cron)
                cron = self.env['ir.cron'].search([('argument', '=','vex_cron' ),("active", "=", False)])
                if cron:
                    try:
                        cron.active = True
                    except:
                        a = 1
        return 0

    def get_category(self,id_cat):
        category_url = "https://api.mercadolibre.com/categories/{}".format(id_cat)
        #raise ValidationError(category_url)
        resx = requests.get(category_url).json()
        '''
        if resx['children_categories']:
            resx['children_categoriesx'] = []
            json_categoryx = []
            c = 0
            for r in resx['children_categories']:
                if c <= 2:
                    json_categoryx.append(self.get_category(r['id']))
                c += 1
            resx['children_categoriesx'].append(json_categoryx)
        '''
        return resx
    @api.model
    def meli_api(self, server, query, accion,filtro,offset=None):
        finish_loop = False
        if query == "products":

            lines_wait = self.env['vexlines.import'].search([('accion', '=', accion.id),
                                                             ('instance', '=', server.id),
                                                             ('instance', '=', server.id), ('state', '=', 'wait')],
                                                            limit=1)
            #raise ValidationError(lines_wait)
            if not lines_wait:
                lw = self.env['vexlines.import'].search([('accion', '=', accion.id),
                                                             ('instance', '=', server.id),
                                                             ('instance', '=', server.id), ('state', '=', 'done')],
                                                            limit=1)
                if lw:
                    finish_loop = True
                    self.env['vexlines.import'].search(
                        [('accion', '=', accion.id), ('instance', '=', server.id)]).unlink()
                #update_cron = "UPDATE ir_cron SET active = 'f'  WHERE argument = 'vex_cron' ".format(server.id)
                #self.env.cr.execute(update_cron)


            res = None
            array_products = []
            if lines_wait:
                #raise ValidationError(lines_wait)
                item_str = lines_wait.url

                res = item_str.split(',')
                #raise ValidationError(res)

                lines_wait.state = 'done'

            else:
                products_url = '{}/users/{}/items/search?search_type=scan&access_token={}'.format(API_URL,
                                                                                              str(server.user_id),
                                                                                              str(server.access_token))
                res = requests.get(products_url).json()
                self.insert_import_lines(server,accion,products_url,res)
                res = res[filtro]

            for r in res:
                #raise ValidationError(str(r))
                item = self.get_data_id(r, server,query)
                array_products.append(item)


            # string_items = ','.join(res)
            # item_url = '{}/items?ids={}&access_token={}'.format(API_URL,string_items,server.access_token)
            # raise ValidationError(item_url)
            # items = requests.get(item_url).json()


            return {
                'data': array_products,
                'finish_loop': finish_loop
            }
        if query == 'categories':
            categories_url = "https://api.mercadolibre.com/sites/{}/categories".format(server.meli_country)
            json_category = []
            res = requests.get(categories_url).json()
            for r in res:
                json_category.append(self.get_category(r['id']))
            #raise ValidationError(str(json_category))
            return {
                'data': json_category,
                'finish_loop': finish_loop
            }
        if query == "orders":
            if offset == None:
                offset = server.last_number_import
                #if offset > 0:
                offset = offset  + 50

            orders_url = '{}/orders/search?seller={}&access_token={}&offset={}'.format(API_URL, str(server.user_id),
                                                                             str(server.access_token),offset)


            if server.order_after:
                datex = server.order_after
                mes = datex.month
                if mes < 10:
                    mes = '0'+str(mes)
                dayx =  datex.day
                if dayx < 10:
                    dayx = '0'+str(dayx)
                #datxstr = f'''{datex.year}-{mes}-%{datex.day}T00:00:00'''
                datxstr = f'''{datex.year}-{mes}-{dayx}T00:00:00.000-04:00'''
                #raise ValueError(datxstr)
                orders_url += f'''&order.date_created.from={datxstr}'''
            _logger.info(F'URL: %s {orders_url}')
            #raise ValidationError(orders_url)
            res = requests.get(orders_url)
            res = res.json()

            if not res[filtro]:
                finish_loop = True
                server.last_number_import = 0

            #raise ValidationError(str([len(res['results']),str(res['results'])]))

            return {
                'data': res[filtro],
                'finish_loop': finish_loop ,
                'res': res ,
                'offset': offset
            }


    def get_total_data_count(self):
        res = super(MeliActionSynchro, self).get_total_data_count()
        return res

    def import_by_parts(self,server,query):
        res = super(MeliActionSynchro, self).import_by_parts(server,query)
        if server.conector == 'meli':
            data_request = self.meli_api(server, query, 'results')
            import json
            raise ValidationError(json.dumps(data_request))
        return res

    def get_total_count(self):
        res = super(MeliActionSynchro, self).get_total_count()
        return res

    def json_fields(self,data,query,server,accion=None):
        res = super(MeliActionSynchro, self).json_fields(data,query,server)
        if server.conector == 'meli':

            create = {}
            write = {}
            if query == "products":
                #raise ValueError(str(data))
                if not 'body' in data:
                    import json
                    raise ValidationError('ka')
                    #raise ValidationError('no existe body in data')
                body = data['body']
                #raise ValidationError(str(body['attributes']))

                active = "'t'" if body['status'] == 'active' else "'f'"
                condicion = "'" + body['condition'] + "'" if body['condition'] else "' '"

                if not server.categ_id:
                    raise ValidationError('not indicate category product')

                #raise ValidationError(str(data))


                #if body['id'] == 'MLM1650434284':
                #    raise ValidationError(str(data))


                create = {
                    'conector': "'meli'",
                    #'server_vex': server.id,
                    'id_vex': "'"+body['id']+"'",
                    'name': "'"+body['title']+"'",
                    'list_price': body['price'] if body['price'] else 0,
                    'type': "'product'",
                    'detailed_type': "'product'",
                    'categ_id': server.categ_id.id,
                    #'is_published': active,
                    'product_condition': condicion,
                    'active_meli': active,
                    'permalink': "'{}'".format(body['permalink']),
                    'base_unit_count': 0,
                    'create_of_meli': "'t'"
                    #'default_code': "'" + body['id'] + "'",
                    #'public_categ_ids': [(6, 0, [self.check_categories(body['category_id'], server, None).id])]
                }
                write = {
                    #'name': "'" + body['title'] + "'",
                    'list_price': body['price'],
                    'type': "'product'",
                    'detailed_type': "'product'",
                    #'categ_id': server.categ_id.id,
                    'permalink': "'" + body['permalink']+ "'",
                    'product_condition':  condicion,
                    'active_meli': active,
                    #'default_code': "'" + body['id'] + "'",
                    'id_vex': "'" + body['id'] + "'",
                    'conector': "'meli'",
                }

                if 'attributes' in body:
                    for atributes in body['attributes']:
                        if atributes['id'] == 'SELLER_SKU':
                            create['default_code'] = f"'{atributes['value_name']}'"
                            write['default_code'] = f"'{atributes['value_name']}'"
                #raise ValidationError(str(create))

            if query == "orders":
                #raise ValidationError(str(data))
                d = str(data['date_created']).split('.')

                fecha = datetime.strptime(d[0], '%Y-%m-%dT%H:%M:%S')
                #raise ValidationError(fecha)

                fecha = fecha + timedelta(hours=3)

                pricelist = server.pricelist
                if not pricelist:
                    raise ValidationError("Set Up pricelist")
                salesteam = server.sales_team
                if not salesteam:
                    raise ValidationError("Set Up Sales Team")
                if not server.warehouse:
                    raise ValidationError("Set Up Warehouse")
                dx = {'customer':{}}

                #id_customer = str(data['buyer']['id'])
                #url_customer = f'''https://api.mercadolibre.com/users/{id_customer}'''

                #item = requests.get(url_customer,params={'access_token': server.access_token}).json()

                #url_envio = f'''https://api.mercadolibre.com/shipments/{str(data['shipping']['id'])}'''

                #envio = requests.get(url_envio,params={'access_token': server.access_token}).json()

                #raise ValidationError(str(envio))

                #nam = "{}".format(str(data['buyer']['nickname']))
                nam = 'Cliente Mercado Libre'
                dx['customer']['name'] , dx['customer']['display_name'] = nam , nam
                if 'phone' in dx['customer']:
                    dx['customer']['phone'] = "'{}'".format(str(data['buyer']['phone']['area_code'])+"-"+str(data['buyer']['phone']['number']))

                customer = self.check_customer(dx, server , data['buyer']['id'] ,accion)
                #raise ValueError(customer)
                sqx = server.sequence_id
                if not sqx:
                    raise ValidationError('sequence not found in instance')
                seq = self.env['ir.sequence'].next_by_code(sqx.code)
                #state = self.env['vex.instance.status.orders'].search([('instance','=',server.id),('value','=',data['status'])])
                #INSERT INTO  sale_order ( team_id, conector, server_vex, id_vex, client_order_ref, name, partner_id, partner_invoice_id, partner_shipping_id, pricelist_id, date_order, create_date, amount_untaxed, amount_total, meli_status, meli_shipping_id, payment_term_id, picking_policy, warehouse_id, state, company_id, meli_pack_id) VALUES ( 7, 'meli', 1, '2000004527802317', '2000004527802317', 'S317987', 6874, 6874, 6874, 1, '2023-06-10 00:33:00', '2023-06-10', 44.99, 44.99, 'paid', '42343914557', 1, 'direct', 1, 'draft', 1, '2000004527802317') ;

                #if state:
                #    state =state.odoo_state
                #    #raise ValidationError(state)
                #else:
                #    state = 'draft'
                #raise ValidationError(state)

                pack_id = data['pack_id']
                id_meli = data['id']
                if pack_id:
                    id_meli = pack_id


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
                    'date_order': "'"+str(fecha)+"'",
                    'create_date': "'" + str(fecha.date()) + "'",
                    'amount_untaxed': float(data['total_amount']),
                    'amount_total': float(data['total_amount']),
                    'meli_status': "'"+str(data['status']) + "'",
                    'meli_shipping_id': "'"+str(data['shipping']['id']) + "'",
                    #'team_id': salesteam.id,
                    #'woo_date_created': "'"+str(data['date_created']) + "'",
                    #'woo_payment_method': "'"+str(data['payment_method_title']) + "'",
                    'payment_term_id': server.payment_term.id,
                    'picking_policy': "'" + str(server.picking_policy) + "'",
                    'warehouse_id': server.warehouse.id,
                    'state': "'draft'",
                    'company_id' : server.company.id ,

                }

                write = {
                    #'state': "''".format(state),
                    'client_order_ref': "'" + str(data['id']) + "'",
                    'meli_status': "'" + str(data['status']) + "'",
                    'date_order': "'" + str(fecha) + "'",
                }

                if pack_id:
                    create['meli_pack_id'] = "'" + str(pack_id) + "'"
                    write['meli_pack_id'] ="'" + str(pack_id) + "'"

                #raise ValidationError(str(write))
            if query == "categories":
                create = {
                    'conector': "'meli'",
                    #'server_vex': server.id,
                    'name': "'"+data['name']+"'",
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

    def import_all(self,server,accion,queryx = ''):

        finish_loop = False
        #raise ValidationError('ohhhh')

        if server.conector == 'meli':
            query = str(accion.argument)
            #raise ValidationError('whatt')
            rt = self.meli_api(server, query,accion ,'results')
            data_request = rt['data']
            finish_loop = rt['finish_loop']
            
            #raise ValueError(str(rt))
            #self.synchro_threading(data_request,query, server, str(accion.model), accion, None , api)
            # importar stock
            data = data_request
            if accion.argument == 'products':
                products = []
                ids_vex = []


                for d in data:
                    #raise ValidationError('ok:'+str(d['body']))
                    #raise ValidationError(str(d['body']))
                    #if d['body']['status'] == 'active':
                    continue_d = True
                    #meli_logistic_type = d['body']['shipping']['logistic_type']
                    #raise ValueError(meli_logistic_type)
                    try:
                        meli_logistic_type =  d['body']['shipping']['logistic_type']
                        if meli_logistic_type == 'fulfillment' and server.not_products_full:
                            continue_d = False
                    except:
                        pass
                   

                    if continue_d:
                        id_vex = d['body']['id']

                        #raise ValidationError(str(d['varitions']))
                        queryx += self.synchro(d, query, server, str(accion.model), accion, id_vex, None)
                        #if accion.stock_import:
                        #   pro = self.env['product.template'].search([('id_vex', '=', str(id_vex))])
                        #    products.append(pro)


                #raise ValidationError(ids_vex)
                if accion.stock_import:
                    self.import_stock(server, products)

            elif accion.argument == 'orders' and data :

                ids_orders_meli = []
                #raise ValidationError(str(rt))
                for d in data:
                    id_meli = d['id']
                    pack_id = d['pack_id']
                    if pack_id:
                        id_meli = pack_id
                    #    raise ValidationError(str(d))


                    _logger.info(f'''id: %s {d['id']}''')
                    if not d['id'] in ids_orders_meli:
                        ids_orders_meli.append(d['id'])
                    self.synchro(d, query, server, str(accion.model), accion, id_meli, None)

                #raise ValueError('uuu')

                #get offsets
                total_offset = rt['res']['paging']['total']
                total_offset = total_offset / 51
                total_offset = math.ceil(total_offset) - 1
                #total_offset = rt['offset '] + accion.per_page

                ctd = rt['offset']


                #for n in range(accion.per_page):
                for n in range(total_offset):
                    ctd = ctd + 50
                    #_logger.info(F'CTD: %s {ctd}')
                    #raise ValueError(ctd)
                    #time.sleep(5)
                    ret = self.meli_api(server, query, accion, 'results', ctd)

                    data_requestx = ret['data']
                    _logger.info(F'''IDR: %s , %S {len(data_requestx), ctd}''')
                    if not data_requestx:
                        ctd = 0
                        break
                    for d in data_requestx:
                        if not d['id'] in ids_orders_meli:
                            ids_orders_meli.append(d['id'])
                            id_meli = d['id']
                            pack_id = d['pack_id']
                            if pack_id:
                                id_meli = pack_id
                            self.synchro(d, query, server, str(accion.model), accion, id_meli, None)
                        else:
                            _logger.info(F'''IDR: %s , %S {d['id'],ctd}''')



                #total_orders = self.env['sale.order'].search_count([('conector','=','meli')])

                #raise ValueError([ctd, total_orders,len(ids_orders_meli)])
                server.last_number_import = ctd



                #raise ValidationError(str(total_offset))

                #raise ValidationError(str(data_requestx))

                # raise ValidationError(total_offset)


            else:
                for d in data:
                    self.synchro(d, query, server, str(accion.model), accion, d['id'], None)
            return finish_loop
        res = super(MeliActionSynchro, self).import_all(server, accion,queryx)
        return res

    def synchro(self, data, query, server, table, accion,id_vex ,api,queryx='',default_code=None):

        if server.conector == 'meli':
            if query == "products":
                
                data['body']['variantes'] = []
                if 'variations' in data['body']:
                    if data['body']['variations']:
                        for varirition in data['body']['variations']:
                            url = f'''https://api.mercadolibre.com/items/{data['body']['id']}/variations/{varirition['id']}?access_token={str(server.access_token)}'''
                            resv = requests.get(url)
                            resv = resv.json()
                            data['body']['variantes'].append(resv)
                            # raise ValidationError(str(resv))
                #raise ValidationError(str(data))
                try:
                    data = data[0]
                except:
                    data = data

                body = data['body']



                if 'attributes' in body:
                    for atributes in body['attributes']:
                        if atributes['id'] == 'SELLER_SKU':
                            default_code = atributes['value_name']

                #raise ValidationError(str([default_code,body]))

            #if query == "products" and server.import_products_paused == False:
            #    if dr['body']['status'] != 'active':
            #       continue

            try:
               id_vex = data['body']['id'] if query == "products" else data['id']
               if  query == 'orders':
                   if data['pack_id']:
                       id_vex = data['pack_id']
            except:
                raise ValueError([id_vex,data])

            if query == "categories":
                if not server.meli_country:
                    raise ValidationError('select country meli')
                data['domain'] = [('id_vex', '=', str(id_vex)), ('conector', '=', 'meli')]




        res = super(MeliActionSynchro, self).synchro(data, query, server, table, accion, id_vex, api,queryx ,default_code)
        return res


    def synchro_ext(self,dr, query, server, table, accion, id_vex , api ,exist,queryx='',sku=False):
        
        if server.conector == 'meli':
            if query == "products":

                queryx += self.insert_variations(dr['body'], server, exist,accion,sku)
                #raise ValueError([exist.id_vex, exist.product_variant_ids])


                if accion.import_images:
                    # insertar la imagen del producto
                    try:
                        url = dr['body']['thumbnail']
                        exist.write({
                            'image_1920': base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b''),
                        })
                    except:
                        return
                if accion.import_images_website:
                    if accion.import_images_website in ['save','dowload']:
                        returnnnn = self.check_imagenes(dr['body']['pictures'], server, exist)

                        if returnnnn:
                            self.env.cr.execute(returnnnn)
                        if accion.import_images_website in ['dowload']:
                            #raise ValidationError(exist.product_template_image_ids)
                            h = self.env['product.image'].search([('product_tmpl_id', '=', exist.id )])
                            if h:
                                h.dowloand_write_img()



                #import categories

                if 'category_id' in dr['body']:
                    if dr['body']['category_id']:
                        cat_id = self.env['product.public.category'].search([('id_vex','=',dr['body']['category_id'])])

                        if not cat_id:
                            item = self.get_data_id(dr['body']['category_id'], server, 'categories')

                            self.synchro(item, 'categories', server,'product.public.category', accion, dr['body']['category_id'], None)

                            cat_id = self.env['product.public.category'].search([('id_vex', '=', dr['body']['category_id'])])

                        if exist and len(exist) == 1:
                            queryh = f'''
                                                            INSERT INTO product_public_category_product_template_rel (product_public_category_id,product_template_id)
                                                            VALUES 
                                                            ({cat_id.id},{exist.id}) 
                                                            ON CONFLICT (product_public_category_id,product_template_id) DO NOTHING ;
                                                            '''
                            self.env.cr.execute(queryh)


            if query == "categories":
                #raise ValidationError('ss'+str(dr))
                if 'path_from_root' in dr:
                    if dr['path_from_root']:
                        datavs = []
                        parent_id = None
                        for d  in dr['path_from_root']:
                            #raise ValidationError(pt)
                            dg  = {
                                'name': d['name'],
                                'id_vex': d['id'],
                                'conector': 'meli',
                                #'parent_id': exist.id,

                            }
                            if parent_id:
                                dg['parent_id_vex_tmp'] = d['id']
                            parent_id = d['id']
                            datavs.append(dg)

                        query_fin = '''
                            UPDATE product_public_category c1
                            SET parent_id = c2.id ,
                            parent_id_vex_tmp = NULL 
                            FROM  (SELECT ct.id FROM product_public_category ct  WHERE ct.parent_id_vex_tmp = ct.id_vex ) as c2
                            WHERE c1.parent_id_vex_tmp IS NOT NULL  ;
                                '''

                        datars = {
                            'model': 'product.public.category',
                            'data': datavs,
                            'identiquer_keys': ['id_vex', 'conector'],
                            'execute_query_end': query_fin

                        }
                        self.env['vex.web.services'].create_update(datars)


                if 'children_categories' in dr:
                    if dr['children_categories']:
                        datav = []
                        for d  in dr['children_categories']:
                            #raise ValidationError(pt)
                            if not exist.id:
                                raise ValidationError(d['name'])
                            namex = d['name']
                            namex = namex.replace("'","")
                            datav.append({
                                'name': namex ,
                                'id_vex': d['id'],
                                'conector': 'meli',
                                'parent_id': exist.id,
                                #'parent_path': pt
                            })
                        datar = {
                            'model': 'product.public.category',
                            'data': datav ,
                            'identiquer_keys': ['id_vex','conector']

                        }
                        self.env['vex.web.services'].create_update(datar)


            if query == 'orders':
                #raise ValueError(exist)
                id_customer = str(dr['buyer']['id'])
                #raise ValidationError(id_customer)
                #_logger.info(F'CREADO VENTA: %s {exist.id}')

                pack_id = dr['pack_id']
                id_meli = dr['id']
                id_meli_origin = id_meli
                if pack_id:
                    id_meli = pack_id

                exist_lines = exist.order_line

                if pack_id  and exist.state == 'draft':
                    #raise ValueError('okkk')
                    exist_lines = self.env['sale.order.line'].search([
                        ('meli_shop_id','=',dr['id']),('order_id','=',exist.id)
                    ])
                #raise ValueError([exist,exist_lines,exist.id_vex,exist.meli_pack_id,pack_id,id_meli_origin])

                if not  exist_lines :
                    #raise   ValidationError('whatss')

                    if pack_id:
                        enviop = self.envio_meli(dr, query, server, exist,True)
                        #raise ValueError(enviop)
                        total_fee = 0
                        if server.discount_fee:
                            total_fee = self.insert_fee_lines(dr['order_items'], exist, server, 'listing_type_id',
                                                              'sale_fee', -1)
                        create_lines = self.insert_lines(dr['order_items'], server, exist, accion, dr['id'],enviop,total_fee)
                    else:
                        create_lines = self.insert_lines(dr['order_items'], server, exist, accion, dr['id'])
                        if server.discount_fee:
                            total_fee = self.insert_fee_lines(dr['order_items'], exist, server, 'listing_type_id',
                                                              'sale_fee', -1)


                    if not create_lines:
                        return ''
                    

                    self.insert_meli_payment(dr['payments'], server, exist, accion)
                    if not pack_id:
                        self.envio_meli(dr, query, server, exist)
                    else:
                        envioz = 0
                        feez = 0
                        for linef in exist.order_line:
                            envioz +=  linef.shipping_vex
                            feez +=  linef.fee_vex
                            
                        #raise ValueError(feez)
                        exist.shipping_vex = envioz
                        exist.fee_vex = feez


                  
                else:
                    
                    if server.print_shipping_with_error:
                        
                        self.envio_meli(dr,query,server,exist)
                        
                #raise ValueError('okk')
                

                if not exist.state:
                    exist.state = 'draft'

                if not pack_id:
                    exist.order_validate_state_meli()




        res = super(MeliActionSynchro, self).synchro_ext(dr, query, server, table, accion, id_vex, api, exist,queryx,sku)

        return res

    #def execute_after_create(self, data, query, server, table, accion, id_vex, api, exist, queryx, is_exist_sku):

    def envio_meli(self,data, query, server , exist , return_cost=False):
        if server.conector == 'meli':
            if query == 'orders':

                id_customer = str(data['buyer']['id'])
                # raise ValidationError(str([exist.partner_id.id_vex,id_customer]))
                if exist.partner_id.id_vex == id_customer :

                    #url_envio = f'''https://api.mercadolibre.com/shipments/{str(data['shipping']['id'])}/cost'''
                    url_envio = f'''https://api.mercadolibre.com/orders/{str(data['id'])}/shipments'''
                    envio = requests.get(url_envio, params={
                        'access_token': server.access_token,
                        'x-format-new': True ,
                        #'x-costs-new' : True
                    }).json()
                    #raise ValidationError(str(envio))
                    if server.print_shipping_with_error:
                        raise ValueError(envio)

                    enviox = envio['base_cost'] if 'base_cost' in envio else 0
                    if 'receiver_address' in envio:
                        name_customer = envio['receiver_address']['receiver_name'] if 'receiver_name' in envio[
                            'receiver_address'] else None
                        if name_customer:
                            exist.partner_id.name = name_customer
                        receiver_phone = envio['receiver_address']['receiver_phone'] if 'receiver_phone' in envio[
                            'receiver_address'] else None
                        if receiver_phone:
                            exist.partner_id.phone = receiver_phone

                        zip_code = envio['receiver_address']['zip_code'] if 'zip_code' in envio[
                            'receiver_address'] else ''
                        exist.partner_id.zip = zip_code

                        neighborhood = envio['receiver_address']['neighborhood']['name'] if 'neighborhood' in envio[
                            'receiver_address'] else ''

                        street_line = envio['receiver_address']['street_name'] if 'street_name' in envio[
                            'receiver_address'] else ''
                        street_number = envio['receiver_address']['street_number'] if 'street_number' in envio[
                            'receiver_address'] else ''
                        country = envio['receiver_address']['country']['name'] if 'country' in envio[
                            'receiver_address'] else ''
                        city = envio['receiver_address']['city']['name'] if 'city' in envio['receiver_address'] else ''
                        state = envio['receiver_address']['state']['name'] if 'state' in envio[
                            'receiver_address'] else ''

                        direccion = f''' {street_line}   {street_number}   {neighborhood}  {state} , {city} ,  {country}  '''
                        exist.partner_id.street = direccion

                        comment = envio['receiver_address']['comment'] if 'comment' in envio['receiver_address'] else ''
                        exist.partner_id.street2 = comment
                        if 'logistic_type' in envio:
                            exist.meli_logistic_type = envio['logistic_type']

                        # raise ValidationError(str(envio))

                    if return_cost:
                        return enviox
                    else:
                        exist.shipping_vex = enviox
                        
    def start_sync_sale_meli(self):
        #importar solo info de productos
        servers = self.env['vex.instance'].search([('active_automatic', '=', True)])
        #raise ValidationError(servers)
        for s in servers:
            self.env['vex.synchro'].check_synchronize(s)
            #wizard = self.env['vex.synchro'].create(dict(
            #    server_vex=s.id,
            #    accion=self.env.ref('linio_connector_vex.linio_action_products', False).id ,
            #    conector='linio',
            #    type_log='automatic'
            #))
            #raise ValidationError()
            #wizard.start_import()

            wizard = self.env['vex.synchro'].create(dict(
                server_vex=s.id,
                accion=self.env.ref('odoo-mercadolibre.meli_action_orders', False).id,
                conector='meli',
                type_log='automatic'

            ))
            wizard.start_import()



        #iniciar la importacion de las ventas
        return

    def start_sync_stock_meli(self):

        sql = ' SELECT id_vex FROM product_template WHERE id_vex IS NOT NULL GROUP BY id_vex;'
        self.env.cr.execute(sql)
        res = self._cr.dictfetchall()
        for re in res:
            product = self.env['product.product'].search([('id_vex','=',re['id_vex']),('id_vex_varition','!=',False),('meli_logistic_type','!=','fulfillment')],limit=1)
            #raise ValueError(product)
            
            if product:
                product.update_conector_vex(False)

    def meli_validate_status_pending_orders(self):
        orders = self.env['sale.order'].search([('state','=','draft'),('id_vex','!=',False),('conector','!=',False)])
        orders.order_validate_state_meli()

    def start_import(self):
        res = super().start_import()
        for i in range(5):
            self.meli_validate_status_pending_orders()
        
        return res


