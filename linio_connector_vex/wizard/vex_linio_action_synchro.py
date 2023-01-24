import requests
import threading
import base64

from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError

import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

id_api       = 'id_vex'
server_api   = 'server_vex'
#API_URL = 'https://sellercenter-api.linio.com.pe'

identify_empty = ''

class LinioActionSynchro(models.TransientModel):
    _inherit = "vex.synchro"

    def synchronize(self, accion, server, bypart=False):
        if server.conector == 'linio':
            if accion.argument == 'products':
                if accion.stock_import:
                    accion.per_page = 520
                    bypart = True
                if accion.import_images:
                    bypart = True
                    accion.per_page = 30
            if accion.argument == 'orders':
                bypart = True


        res =  super(LinioActionSynchro, self).synchronize(accion, server, bypart)
        acciones = self.env['vex.restapi.list'].search([])
        if bypart:
            #for a in acciones:
            #    a.active_cron = False
            servers = self.env['vex.instance'].search([])
            #for s in servers:
            #    s.active_automatic = False
            #accion.active_cron = True
            #server.active_automatic = True

            if accion.argument == 'orders':
                if res:
                    return res
            else:
                cron = self.env.ref('base_conector_vex.vex_soluciones_ir_cron_automatico', False)
                if not cron.active:
                    cron.active = True


        server.active_list = accion.id

        if accion.argument == 'orders':
            if res:
                server.active_list = False



        return  res


    def import_by_parts(self,server,accion,query):

        if server.conector == 'linio':
            query = str(accion.argument)
            rt = self.vex_api(server, query, accion, 'results')
            if query == 'orders':

                #raise ValidationError(str(rt))
                data_request = rt['data']
                #raise ValidationError(str(data_request))
                c = 0
                if not data_request:
                    return True
                max_items = len(data_request)
                #raise ValidationError(str(max_items))
                # array_new = []
                #recorremos la data
                if 'OrderId' in data_request:
                    r = data_request
                    res2 = server.api_get_linio('GetOrderItems', others=dict(OrderId=r['OrderId'])).json()
                    r['items'] = res2['SuccessResponse']['Body']['OrderItems']['OrderItem']
                    self.synchro(r, query, server, str(accion.model), accion, r['OrderId'], None)
                    max_items = 1
                else:
                    for r in data_request:
                        c += 1
                        #if c >= max_items:
                        #    c = 0
                        #    raise ValidationError(str([c,max_items]))
                        #    #server.active_automatic = False
                        #if c > accion.per_page + accion.last_number_import:
                        #    break

                        # raise ValidationError(str(r))

                        res2 = server.api_get_linio('GetOrderItems', others=dict(OrderId=r['OrderId'])).json()
                        r['items'] = res2['SuccessResponse']['Body']['OrderItems']['OrderItem']
                        self.synchro(r, query, server, str(accion.model), accion, r['OrderId'], None)
                        # array_new.append(r)
                    # raise ValidationError(str([c,max_items]))




                accion.last_number_import = c - 1 if c > 0 else 0


                if accion.per_page <= max_items:
                    return True
                else:
                    return False


            if query == 'products':
                data_request = rt['data']['SuccessResponse']['Body']['Products']['Product']
                c = 0

                max_items = len(data_request)
                # array_new = []
                ids_vex = []

                data = self.organize_data(data_request)
                for d in data:
                    c += 1
                    if c >= max_items:
                        c = 0
                        server.active_automatic = False
                    if c > accion.per_page + accion.last_number_import:
                        break

                    id_vex = d['SellerSku']

                    self.synchro(d, query, server, str(accion.model), accion, id_vex, None)
                    ids_vex.append(id_vex)
                    # array_new.append(r)


                if accion.stock_import:
                    products = self.env['product.template'].search(
                        [('id_vex', 'in', ids_vex), ('server_vex', '=', server.id)])
                    self.import_stock(server, products)
                accion.last_number_import = c - 1 if c > 0 else 0


                # raise ValidationError(str(res2))
            #raise ValidationError(str(array_new))
        else:
            return super(LinioActionSynchro, self).import_by_parts(server, query, server)


    def start_import(self):
        res = super(LinioActionSynchro, self).start_import()
        if self.conector == 'linio':
            id_action = 'linio_connector_vex.action_view_linio_synchro'
            return self.vex_import(id_action,None)
        return res


    #organize data x variantes
    def organize_data(self,data):
        #raise ValidationError(str(data))
        new_data = {}
        #array_parent = []
        for d in data:
            #if not d['ParentSku'] in array_parent:
            #    array_parent.append(d['ParentSku'])
            if d['ParentSku'] not in new_data:
                if d['ParentSku'] == d['SellerSku']:
                    new_data[d['ParentSku']] = d
                    if new_data[d['ParentSku']]['Variation'] == '...':
                        new_data[d['ParentSku']]['variantes'] = []
                    else:
                        new_data[d['ParentSku']]['variantes'] = []
                        new_data[d['ParentSku']]['variantes'].append(d)

                else:
                    if not 'variantes' in d['ParentSku']:
                        new_data[d['ParentSku']]['variantes'] = []
                    new_data[d['ParentSku']]['variantes'].append(d)
            else:
                if not 'variantes' in d['ParentSku']:
                    new_data[d['ParentSku']]['variantes'] = []
                new_data[d['ParentSku']]['variantes'].append(d)

        new_new_data = []

        for n in new_data:
            new_new_data.append(new_data[n])

        #raise ValidationError(str(new_data))


        return new_new_data



    def get_data_init(self,server,accion,query):
        #raise ValidationError('oqueee')
        res = super(LinioActionSynchro, self).get_data_init(server,accion,query)
        if server.conector == 'linio':
            #raise ValidationError('h')
            if query == "products":
                #raise ValidationError('ok')
                #others = {'Limit': 10, 'Filter': 'live'}
                res = server.api_get_linio('GetProducts').json()
                #res = self

                return res

            if query == "orders":

                #raise ValidationError(str(res))

                if server.order_after:
                    f = str(server.order_after) if server.use_date_specific else str(server.order_after_days)
                    f = f.replace(' ','T')
                    #raise ValidationError(f)
                    res = server.api_get_linio('GetOrders',{
                        'CreatedAfter': f ,
                        #'Status':  'delivered,canceled,returned,canceled,failed'
                    }).json()
                    '''
                    resx = res
                    res = []
                    for data in resx:
                        d = str(data['CreatedAt'])
                        # raise ValidationError(d[0])
                        fecha = datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
                        if fecha >= server.order_after:
                            res.append(data)
                    '''
                else:
                    res = server.api_get_linio('GetOrders').json()
                try:
                    res = res['SuccessResponse']['Body']['Orders']['Order']
                except:
                    return None


                return res

            if query == "categories":
                return server.api_get_linio('GetCategoryTree').json()
                #return self.get_category(id_vex)
                #raise ValidationError(str(res))
            #raise ValidationError(str(item))

        return res


    def import_all(self,server,accion,queryx = ''):

        finish_loop = False
        #raise ValidationError('ohhhh')

        if server.conector == 'linio':
            #raise ValidationError('lito')
            query = str(accion.argument)
            #raise ValidationError('whatt')



            rt = self.vex_api(server, query,accion ,'results')
            #raise ValidationError('pipip'+str(rt))
            data_request = rt['data']
            finish_loop = rt['finish_loop']

            data_request = data_request['SuccessResponse']['Body']

            #raise ValidationError(str(data_request))
            #self.synchro_threading(data_request,query, server, str(accion.model), accion, None , api)
            # importar stock
            if accion.argument == 'products':
                products = []
                ids_vex = []
                data = data_request['Products']['Product']
                data = self.organize_data(data)
                for d in data:
                    #raise ValidationError(str(d))
                    id_vex = d['SellerSku']
                    queryx += self.synchro(d, query, server, str(accion.model), accion, id_vex, None)
                    ids_vex.append(id_vex)
                    #pro = self.env['product.template'].search([('id_vex','=',str(id_vex))])
                    #products.append(pro)
                #raise ValidationError(ids_vex)

                if accion.stock_import:
                    products = self.env['product.template'].search(
                        [('id_vex', 'in', ids_vex), ('server_vex', '=', server.id)])
                    self.import_stock(server, products)

            if accion.argument == 'categories':
                data = data_request['Categories']['Category']
                #raise ValidationError(str(data))
                for d in data:
                    #raise ValidationError(str(d))
                    id_vex = d['Name']
                    self.synchro(d, query, server, str(accion.model), accion, id_vex, None)
            return finish_loop
        res = super(LinioActionSynchro, self).import_all(server, accion,queryx)
        return res


    def synchro(self, data, query, server, table, accion,id_vex ,api=None,queryx = '',default_code=None):
        if server.conector == 'linio':
            if query == "products":
                id_vex = data['SellerSku']
                default_code = id_vex

            if query == "categories":
                #id_vex = data['Name']
                data['domain'] = [('name', '=', str(data['Name'])), ('conector', '=', 'linio'),
                                  ('id_vex','=',data['GlobalIdentifier'])]


        res = super(LinioActionSynchro, self).synchro(data, query, server, table, accion, id_vex, api,queryx,default_code)
        return res


    def json_fields(self,data,query,server,accion=None):
        resx = super(LinioActionSynchro, self).json_fields(data,query,server,accion)
        if server.conector == 'linio':

            create = {}
            write = {}
            if query == "products":
                body = data

                if not server.categ_id:
                    raise ValidationError("linio instance, products' category not indicated")

                create = {
                    'conector': "'linio'",
                    #'server_vex': server.id,
                    'id_vex': "'"+body['SellerSku']+"'",
                    'name': "'"+body['Name']+"'",
                    'list_price': body['Price'] if body['Price'] else 0,
                    'detailed_type': "'product'",
                    'type': "'product'",
                    'categ_id': server.categ_id.id or 'NULL',
                    #'is_published': active,
                    #'product_condition': condicion,
                    #'active_meli': active,
                    'permalink': "'{}'".format(body['Url']),
                    'base_unit_count': 0 ,
                    #'default_code': f"'{body['ShopSku']}'",
                    'default_code': "'" + body['SellerSku'] + "'",
                    'description': f"'{body['Description']}'",

                    #'public_categ_ids': [(6, 0, [self.check_categories(body['category_id'], server, None).id])]
                }
                if not server.share_multi_instances:
                    create['server_vex'] =  server.id

                #verificar si el modulo compras esta istalado
                is_purchase = self.env['ir.module.module'].search([('name','=','purchase'),('state','=','installed')])
                if is_purchase:
                    create['purchase_line_warn'] = "'no-message'"


                write = {
                    'name': "'" + body['Name'] + "'",
                    'list_price': body['Price'],
                    'detailed_type': "'product'",
                    'type': "'product'",
                    'categ_id': server.categ_id.id or 'NULL',
                    'permalink': "'" + body['Url']+ "'",
                    'default_code': f"'{body['ShopSku']}'",
                    'description': f"'{body['Description']}'",

                    #'product_condition':  condicion,
                    #'active_meli': active,
                }

            if query == "orders":
                d = str(data['CreatedAt'])
                #raise ValidationError(str(data))
                fecha = datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
                pricelist = server.pricelist
                if not pricelist:
                    raise ValidationError("Set Up pricelist")
                salesteam = server.sales_team
                if not salesteam:
                    raise ValidationError("Set Up Sales Team")
                if not server.warehouse:
                    raise ValidationError("Set Up Warehouse")
                dx = {'customer':{} , 'billing': {} , 'shipping': {}}
                nam = "{}".format(str(data['CustomerFirstName']+' '+data['CustomerLastName']))
                dx['customer']['name'] , dx['customer']['display_name'] = nam , nam
                dx['customer']['vat'] = f"{str(data['NationalRegistrationNumber'])}"

                ccc = 0
                for ab in [data['AddressBilling'],data['AddressShipping']]:
                    type_cus = 'billing' if ccc == 0 else 'shipping'
                    nam = "{}".format(str(ab['FirstName'] + ' ' + ab['LastName']))
                    dx[type_cus]['name'] = nam
                    if 'Phone' in ab:
                        dx[type_cus]['phone'] = "{}".format(str(ab['Phone']))
                    if 'Phone2' in ab:
                        dx[type_cus]['mobile'] = "{}".format(str(ab['Phone2']))

                    if 'Address1' in ab:
                        dx[type_cus]['street'] = "{}".format(
                            str(ab['Address1']) + ' '+ str(ab['Address2'])+' '
                            +str(ab['Address3'])+' '+str(ab['Address4'])+' '+str(ab['Address5'])
                            +str(ab['Ward'])+' '+ str(ab['Region']) + str(ab['City']) + ' ' + str(ab['Country']))

                    if 'CustomerEmail' in ab:
                        dx[type_cus]['email'] = "{}".format(str(ab['CustomerEmail']))
                    if 'PostCode' in ab:
                        dx[type_cus]['zip'] = "{}".format(str(ab['PostCode']))
                    ccc += 1


                #raise ValidationError(str(dx)+'---'+str(data))


                customer = self.check_customer(dx, server , str(data['NationalRegistrationNumber']) ,accion)
                #raise ValueError(customer)
                sqx = server.sequence_id
                if not sqx:
                    raise ValidationError('sequence not found in instance')
                seq = self.env['ir.sequence'].next_by_code(sqx.code)

                if 1 == 5:
                    # state = data['Statuses']['Status']
                    state_b = self.env['vex.instance.status.orders'].search(
                        [('instance', '=', server.id), ('value', '=', state)])

                    if state_b:
                        state = state_b.odoo_state
                    else:
                        state = 'draft'

                state = 'draft'

                #raise ValidationError(state)
                create = {

                    'conector': "'linio'",
                    'server_vex': server.id,
                    'id_vex': "'" + str(data['OrderId']) + "'",
                    'name': "'" + str(seq) + "'",
                    'partner_id': customer['customer'].id,
                    'partner_invoice_id': customer['invoice'].id,
                    'partner_shipping_id': customer['shipping'].id,
                    'pricelist_id': server.pricelist.id,
                    'date_order': "'"+str(fecha)+"'",
                    'amount_untaxed': float(data['Price']),
                    'amount_total': float(data['Price']),
                    #'woo_status': "'"+str(['status']) + "'",
                    #'woo_customer_ip_address': "'"+str(data['customer_ip_address']) + "'",
                    'team_id': salesteam.id,
                    #'woo_date_created': "'"+str(data['date_created']) + "'",
                    #'woo_payment_method': "'"+str(data['payment_method_title']) + "'",
                    'payment_term_id': server.payment_term.id,
                    'picking_policy': "'" + str(server.picking_policy) + "'",
                    'warehouse_id': server.warehouse.id,
                    'state': "'{}'".format(state),
                    'company_id' : server.company.id ,
                    'client_order_ref': "'{}'".format(data['OrderNumber']),
                    'user_id': server.user_sale_id.id if server.user_sale_id else None,
                }



                write = {
                   # 'state': "'{}'".format(state),
                  #'date_order': "'" + str(fecha) + "'",
                }

                #raise ValidationError(str(data))

                #if server.discount_fee == 'save':
                #    write['fee_vex'] =

            if query == "categories":
                #raise ValidationError(str(data))
                create = {
                    'conector': "'linio'",
                    #'server_vex': server.id,
                    'name': "'"+data['Name']+"'",
                    #'id_vex': "'" + data['Name'] + "'",
                    #'global_identifier': "'" + data['GlobalIdentifier'] + "'",
                    'id_vex': "'" + data['GlobalIdentifier'] + "'",
                }
                write = create.copy()

                #del write['global_identifier']


            #raise ValidationError(str(resx['create']))

            resx['create'].update(create)
            resx['write'].update(write)
        return resx



    def update_children_linio(self,dr,identify_empty='*'):
        query_fin = ''

        datavs = []
        if 'Children' in dr:
            if dr['Children']:

                #parent_id = None
                #parent_id = dr['Name']
                parent_id = dr['GlobalIdentifier']
                childrens = dr['Children']['Category']
                if 'Name' in childrens:

                    d = dr['Children']['Category']

                    gb_identy = d['GlobalIdentifier']

                    if gb_identy == '' or not gb_identy:
                        identify_empty  += '*'
                        gb_identy = identify_empty


                    dg = {
                        'name': d['Name'],
                        'id_vex': gb_identy ,
                        #'id_vex': d['Name'],
                        #'global_identifier': gb_identy,
                        'conector': 'linio',
                        'parent_id_vex_tmp': parent_id
                        # 'parent_id': exist.id,

                    }

                    dv, qf = self.update_children_linio(d,identify_empty)

                    query_fin += qf
                    if dv:
                        datavs += dv
                    datavs.append(dg)

                else:
                    for d in dr['Children']['Category']:
                        # raise ValidationError(pt)
                        gb_identy = d['GlobalIdentifier']
                        if gb_identy == '' or not gb_identy:
                            identify_empty += '*'
                            gb_identy = identify_empty
                        dg = {
                            'name': d['Name'],
                            'id_vex': gb_identy,
                            #'id_vex':d['Name'] ,
                            #'global_identifier': gb_identy,
                            'conector': 'linio',
                            'parent_id_vex_tmp': parent_id
                            # 'parent_id': exist.id,

                        }

                        dv, qf = self.update_children_linio(d)

                        query_fin += qf
                        if dv:
                            datavs += dv
                        datavs.append(dg)


                query_fin += f'''
                   UPDATE product_public_category c1
                   SET parent_id = c2.id ,
                   parent_id_vex_tmp = NULL 
                   
                   FROM  (SELECT ct.id FROM product_public_category ct  WHERE ct.id_vex = '{parent_id}' ) as c2
                   WHERE c1.parent_id_vex_tmp IS NOT NULL AND c1.parent_id_vex_tmp = '{parent_id}' ;
                   
                   
                   
                       '''

        return datavs , query_fin

    @api.model
    def insert_variations_linio(self, dr, server, creado, accion, queryx=''):
        # recorrer las variantes y chekar todas los atrbutos
        # guardar el id por atributo y luego colocarlo en el respect
        variantes_array = {'ja'}
        values_array = {'ja'}
        # obtener las variantes
        variants = dr['variantes']
        if variants == '...':
            variants = None
        # raise ValidationError(str(len(variants)))

        if variants:
            vi = {
                'id': 'variacion',
                'name': 'Variacion',
                'values': []
            }
            at = self.check_attributes(vi, server)

            if not at:
                raise ValidationError('no se llego a crear el atributo variacion')



            for v in variants:
                data_values_ids = []
                term = [
                    {
                        'name': v['Variation'] ,
                        'id': v['Variation'] ,
                    }
                ]
                self.inser_terminos(term, at, server)

                # buscar si existe el atributo en atribute line
                atl = self.env['product.template.attribute.line'].search(
                    [('attribute_id', '=', int(at.id)), ('product_tmpl_id', '=', int(creado.id))])

                if not atl:
                    data = {
                        ' active ': "'t'",
                        'attribute_id': int(at.id),
                        'product_tmpl_id': int(creado.id),

                    }
                    self.json_execute_create('product.template.attribute.line', data)
                    # currents = self._cr.dictfetchall()
                    # raise ValidationError(currents)
                    atl = self.env['product.template.attribute.line'].search(
                        [('product_tmpl_id', '=', creado.id), ('attribute_id', '=', at.id)])


                if atl:
                    # verificar si existe ese valor  en ese atributo line
                    valores_actuales = atl.value_ids
                    # raise ValidationError(valores_actuales)
                    va_array = []
                    for va in valores_actuales:
                        va_array.append(va.name)
                    # raise ValidationError(va_array)
                    for vx in term:
                        # raise ValidationError(vx)
                        vv = None

                        if not vx['name'] in va_array:
                            #atl.value_ids += at
                            vv = self.check_terminos(vx['name'], server, at, creado)

                            # raise ValidationError('aabt' + str(pppi))
                            # raise ValidationError('que')
                            if vv:
                                atl.value_ids += vv

                        else:
                            vv = self.check_terminos(vx['name'], server, at)
                            # raise ValidationError(vv)

                        if vv:
                            line_v = self.env['product.template.attribute.value'].search(
                                [('product_attribute_value_id', '=', vv.id), ('attribute_id', '=', at.id),
                                 ('product_tmpl_id', '=', creado.id),
                                 ('attribute_line_id', '=', atl.id)])
                            data_values_ids.append(line_v.id)

                        values_array.add(str(at.id) + '_' + vx['name'])
                else:
                    raise ValidationError('error no se llego a crear el atributo line '+str(atl))


                pppi = self.env['product.product'].search(
                    [('product_tmpl_id', '=', int(creado.id)), ('id_vex_varition', '=', False),
                     '|', ('active', '=', True), ('active', '=', False)])

                if pppi:
                    write = {
                        ' active ': "'t'",
                        'id_vex_varition': "'" + str(v['SellerSku']) + "'",
                        'stock_vex': v['Quantity'],
                        'vex_regular_price': v['Price'],
                    }

                    self.json_execute_update('product.product', write, pppi.id)


            #este codigo cuando hay mas de una variante
            '''
            if accion.import_images:
                for index, v in enumerate(variants):
                    ppp = self.env['product.product'].search([('product_tmpl_id', '=', int(creado.id)),

                                                              ('id_vex_varition', '=', str(v['SellerSku'])),
                                                              '|', ('active', '=', True), ('active', '=', False)])

                    url = ''
                    pictures = dr['pictures']
                    for p in pictures:
                        if p['id'] == v['picture_ids'][0]:
                            url = p['url']
                    myfile = requests.get(url)
                    try:
                        myimage = requests.get(url)
                    except requests.ConnectionError:
                        continue
                    # raise ValidationError(ppp)

                    ppp.write({'image_1920': base64.b64encode(myimage.content)})
            '''

            # raise ValidationError(str(insert_vari))

        else:
            # crear product de template
            ppp = self.env['product.product'].search([('product_tmpl_id', '=', int(creado.id)),
                                                      ('id_vex_varition', '=', str(creado.id_vex)),
                                                      '|', ('active', '=', True), ('active', '=', False)])
            if not ppp:
                # 1==1:
                create = {
                    ' active ': "'t'",
                    'product_tmpl_id': creado.id,
                    'id_vex_varition': "'" + str(creado.id_vex) + "'",
                    'stock_vex': dr['Quantity'],
                    'base_unit_count': 0,
                    # 'vex_regular_price': v['price']
                }
                # raise ValidationError(str(dr))
                self.json_execute_create('product.product', create)

        self.invalidate_cache()
        return queryx

    @api.model
    def check_imagenes_linio(self, imagenes, server, product):
        product.product_template_image_ids.unlink()
        # verificar las imagenes
        img_str = ''

        # imagenes_array = {'ja'}

        for i in imagenes:
            data = {
                #id_api: "'{}'".format(image['id']),
                 server_api: server.id,
                'conector': "'{}'".format(server.conector),
                'image_url_vex': "'{}'".format(i),
                'product_tmpl_id': product.id,
                'name': "'{}'".format(product.name),

            }

            #raise ValidationError(str(data))

            img_str = self.json_execute_create('product.image', data, True)
            #img_str += self.check_picture(i, server, exist)
            '''
            imagenes_array.add(imm.id)
            imagenes_odoo_array = {'ja'}
            for ii in exist.product_template_image_ids:
                imagenes_odoo_array.add(ii.id)
            resta = imagenes_odoo_array - imagenes_array
            for r in resta:
                self.env['product.image'].search([('id', '=', int(r))]).unlink()
            '''
        return img_str



    def synchro_ext(self,dr, query, server, table, accion, id_vex , api ,exist,queryx='',is_exist_sku=False):
        #raise ValidationError(exist)
        if server.conector == 'linio':
            if query == "products" and not is_exist_sku :
                #probar codigo
                #raise ValidationError(str(dr))

                queryx += self.insert_variations_linio(dr, server, exist,accion)


                if accion.import_images:
                    # insertar la imagen del producto
                    url = dr['MainImage']
                    if url:
                        try:

                            # raise ValidationError(url)
                            exist.write({
                                'image_1920': base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b''),
                            })
                        except:
                            a = 1

                if accion.import_images and 'Images' in dr :
                    if dr['Images']:
                        #if accion.import_images_website in ['save', 'dowload']:
                        if 1 == 1 :
                            # raise ValidationError(str(dr['Images']['Image']))
                            try:
                                a = dr['Images']['Image']
                            except:
                                raise ValidationError(str((dr['Images'])))
                            returnnnn = self.check_imagenes_linio(dr['Images']['Image'], server, exist)

                            if returnnnn:
                                self.env.cr.execute(returnnnn)
                            #if accion.import_images_website in ['dowload']:
                            if 1 == 1:
                                # raise ValidationError(exist.product_template_image_ids)
                                h = self.env['product.image'].search([('product_tmpl_id', '=', exist.id)])
                                if h:
                                    h.dowloand_write_img()



                #import categories


                if 'PrimaryCategory' in dr:
                    if dr['PrimaryCategory']:
                        cat_id = self.env['product.public.category'].search([('name','=',dr['PrimaryCategory']),('conector','=','linio')])


                        if not cat_id:

                            raise ValidationError('No se Encontro la categoria , asegurese de inportar las categorias primero')
                            #item = self.get_data_id(dr['PrimaryCategory'], server, 'categories')
                            #self.synchro(item, 'categories', server,'product.public.category', accion, dr['body']['category_id'], None)
                            #cat_id = self.env['product.public.category'].search([('id_vex', '=', dr['body']['category_id'])])

                        if len(cat_id) > 1:
                            cat_id = self.env['product.public.category'].search(
                                [('name', '=', dr['PrimaryCategory']), ('conector', '=', 'linio'),('id_vex','not like','*')])
                            if len(cat_id) > 1:
                                #raise ValidationError(str(dr))
                                raise ValidationError(f"se encontro mas de una categoria con el mismo nombre  {dr['PrimaryCategory']} , producto id { exist.display_name}")
                            if not cat_id:
                                cat_id = self.env['product.public.category'].search(
                                    [('name', '=', dr['PrimaryCategory']), ('conector', '=', 'linio')],limit=1)
                                #raise ValidationError(dr['PrimaryCategory'])

                        queryh = f'''
                                INSERT INTO product_public_category_product_template_rel (product_public_category_id,product_template_id)
                                VALUES 
                                ({cat_id.id},{exist.id}) 
                                ON CONFLICT (product_public_category_id,product_template_id) DO NOTHING ;
                                '''
                        self.env.cr.execute(queryh)

            if query == "categories":
                exist.parent_path = str(exist.id) + "/"
                '''
                try:
                    exist.parent_path = str(exist.id) + "/"
                except:
                    #raise ValidationError(exist)
                    raise ValueError([exist[0].id,exist[0].id_vex,exist[1].id,exist[1].global_identifier,dr])
                '''

                datavs , query_fin = self.update_children_linio(dr)

                #raise ValidationError(query_fin)

                datars = {
                    'model': 'product.public.category',
                    'data': datavs,
                    'identiquer_keys': ['name','id_vex', 'conector'],
                    #'identiquer_keys': ['id_vex', 'conector','global_identifier'],
                    'execute_query_end': query_fin

                }
                self.env['vex.web.services'].create_update(datars)

                #update_path  = f'''UPDATE product_public_category SET parent_path = id WHERE parent_id IS NULL '''


            if query == 'orders':




                if not exist.user_id:
                    exist.user_id = server.user_sale_id.id if server.user_sale_id else None


                if exist.state != 'cancel':

                    exist_copy = False
                    type_chipments = []


                    if not exist.order_line:


                        # raise ValidationError(str(dr))
                        # if len(dr['items']) > 1 :
                        #    itemss = dr['items']
                        # if len(dr['items']) == 1 :
                        itemss = dr['items']
                        if 'OrderItemId' in dr['items']:
                            # raise ValidationError(str(dr['items']))
                            itemss = [dr['items']]
                        order_items = self.insert_lines(itemss, server, exist, accion)
                        if server.discount_fee and 5 == 7:
                            # if server.discount_fee == ''
                            total_fee = self.insert_fee_lines(itemss, exist, server, 'listing_type_id',
                                                              'sale_fee', -1)
                            tt = exist.amount_total + float(total_fee)
                            self.json_execute_update('sale.order', {
                                'amount_untaxed': tt,
                                'amount_total': tt
                            }, exist.id)

                            # validar si haymas de dos almcenes

                            for l in exist.order_line:
                                if not l.linio_shippingtype in type_chipments:
                                    type_chipments.append(l.linio_shippingtype)

                        for l in exist.order_line:
                            if not l.linio_shippingtype in type_chipments:
                                type_chipments.append(l.linio_shippingtype)


                        if len(type_chipments) > 1:

                            exist_copy = exist.copy()
                            exist_copy.id_vex = exist.id_vex
                            exist_copy.conector = exist.conector
                            exist_copy.server_vex = exist.server_vex.id
                            exist_copy.primary_order_id = exist.id




                    itemss = dr['items']
                    if 'OrderItemId' in dr['items']:
                        # raise ValidationError(str(dr['items']))
                        itemss = [dr['items']]
                    for l in itemss:
                        order_items = [int()]
                        #type_invoices = ["invoice", "exportInvoice", "shippingLabel", "shippingParcel",
                        #                 "carrierManifest", "serialNumber"]
                        type_invoices = ["shippingParcel"]
                        # raise ValidationError(str(l))
                        for t in type_invoices:
                            res1 = server.api_get_linio('GetDocument', others=dict(
                                DocumentType=t,
                                OrderItemIds=f'''[{l['OrderItemId']}]'''
                            )).json()

                            if 'SuccessResponse' in res1:
                                dmxx = [('type', '=', t),
                                        ('sale_order_line.linio_order_item_id', '=', str(l['OrderItemId'])),
                                        ('sale_order_line.order_id.server_vex', '=', server.id),
                                        ('order_id.primary_order_id', '=', False)
                                        ]
                                existx = self.env['linio.documents.sol'].search(dmxx)
                                if not existx:
                                    ddmx = [('order_id.server_vex', '=', server.id),
                                            ('linio_order_item_id', '=', str(l['OrderItemId'])),
                                            ('product_id.id_vex_varition', '!=', 'shipping_linio'),('order_id.primary_order_id','=',False)]

                                    basetext = res1['SuccessResponse']['Body']['Documents']['Document']['File']
                                    # raise ValidationError(basetext)
                                    # bytes = base64.b64decode(basetext, validate=True)
                                    bytes = basetext

                                    self.env['linio.documents.sol'].create(dict(
                                        sale_order_line=self.env['sale.order.line'].search(ddmx).id,
                                        type=t,
                                        name=str(l['OrderItemId']) + '_' + t + '.pdf',
                                        data=bytes

                                    ))

                    if not exist.create_date:
                        exist.create_date = exist.date_order
                    #exist.create_date = exist.date_order

                    state = dr['Statuses']['Status']
                    stx = None
                    #raise ValidationError(str(state))
                    if isinstance(state, dict) and len(state) > 1 :
                        for s in state:
                            stx = s
                    else:
                        stx = state


                    dmm = [('instance', '=', server.id), ('value', '=', stx)]

                    state_b = self.env['vex.instance.status.orders'].search(dmm)

                    if state_b:
                        if len(state_b) > 1:
                            stsx = ''
                            for s in stx:
                                stsx = s

                            dmm = [('instance', '=', server.id), ('value', '=', stsx)]

                            state_b = self.env['vex.instance.status.orders'].search(dmm)
                            if len(state_b) > 1:
                                raise ValidationError(str(dmm))

                        state = state_b.odoo_state
                    else:
                        state = 'sale'

                    #sql = f'''UPDATE sale_order SET state = '{state}' WHERE id = {exist.id}  ; '''
                    #self.env.cr.execute(sql)

                    #raise ValidationError(str([stx,state,state_b.state,state_b.created_shipment,exist.state]))


                    #if exist.id == 2999:
                    #    raise ValueError([exist_copy])
                    #if dr['OrderId'] == '10852515':
                    #    raise ValidationError(str([state,exist.state,  state_b.created_shipment , exist.order_line, type_chipments ,len(type_chipments)]))
                    if state == 'sale' and  state_b.created_shipment and exist.state not in ['sale','done','cancel'] :
                        #raise ValidationError('que esta pasando aqui')

                        if len(type_chipments) > 1:


                            #primer almacen
                            almacen1 = type_chipments[0]
                            for llx in exist.order_line:
                                if llx.linio_shippingtype != almacen1:
                                    try:
                                        llx.unlink()
                                    except:
                                        raise ValidationError([1,exist.state,exist])

                            exist.warehouse_id = server.warehouse_dropshipping if almacen1 == 'Dropshipping' else server.warehouse_ownwarehouse
                            exist.state = 'draft'
                            exist.action_confirm()

                            almacen2 = type_chipments[1]

                            for llx in exist_copy.order_line:
                                if llx.linio_shippingtype != almacen2:
                                    try:
                                        llx.unlink()
                                    except:
                                        raise ValidationError([2, exist_copy.state,exist_copy.id])
                            exist_copy.state = 'draft'
                            exist_copy.warehouse_id = server.warehouse_dropshipping if almacen2 == 'Dropshipping' else server.warehouse_ownwarehouse
                            exist_copy.action_confirm()


                        else:
                            exist.action_confirm()
                            #raise ValidationError
                            if exist.secundary_order_ids:
                                for osc in exist.secundary_order_ids:
                                    if osc.state not in ['done','cancel']:
                                        osc.action_confirm()



                    else:
                        if state == 'sale' and exist.state not in ['sale','done','cancel'] :
                            exist.action_confirm()
                        else:
                            exist.state = state

                        if exist.secundary_order_ids:
                            for osc in exist.secundary_order_ids:
                                if state == 'sale' and osc.state not in ['sale', 'done', 'cancel']:
                                    osc.action_confirm()
                                else:
                                    osc.state = state
                    #if exist.id == 2999 :
                    #    raise ValidationError('no dx')

                #if dr['OrderId'] == '10852515':
                #    raise ValidationError('okey pillla')




        res = super(LinioActionSynchro, self).synchro_ext(dr, query, server, table, accion, id_vex, api, exist,queryx,is_exist_sku)

        return res



    def check_product_order_linio(self,p  , server , accion):

        if server.search_sku:
            # buscar en product product
            identi = 'default_code'
            #identi = 'id_vex'
            # raise ValidationError('k'+str(p))
            dmi = [(identi, '=', p['Sku']), ('server_vex', '=', int(server.id))]
            if server.share_multi_instances:
                dmi = [(identi, '=', p['Sku']), ('conector', '=', 'linio')]

            pp = self.env['product.product'].search(dmi)

            if not pp:
                raise ValidationError(f'''NO SE ENCONTRO EL PRODUCTO con SKU X LINIO :  {p['Sku']}''')

            return pp




        #raise ValidationError(str(p))
        pp = None


        try:
            atributo = p['Variation']
        except:
            raise ValidationError('no variation:'+str(p))



        #condicion para verificar si es un atributo
        is_atribute = False
        if atributo != '...':
            is_atribute = True
        if is_atribute:

            #buscar en product product
            #identi =  'default_code'
            identi = 'id_vex'
            #raise ValidationError('k'+str(p))
            dmi = [(identi,'=',p['Sku']),('server_vex','=',int(server.id))]
            if server.share_multi_instances:
                dmi = [(identi, '=', p['Sku']), ('conector', '=', 'linio' )]

            pp = self.env['product.product'].search(dmi)
            #raise ValidationError(pp)
            #si no existe crearlo
            if not pp:


                try:
                    self.check_produc(p['id'], server ,accion)
                    ddmx = [(identi, '=', str(atributo)),('server_vex', '=', int(server.id))]
                    if server.share_multi_instances:
                        ddmx = [(identi, '=', str(atributo)), ('conector', '=', 'linio')]
                    pp = self.env['product.product'].search(ddmx)

                    if not pp:
                        raise ValueError('EMPTY DATA')
                except:
                    #crear producto
                    ddmx = [(identi, '=', p['id']), ('server_vex', '=', int(server.id))]
                    if server.share_multi_instances:
                        ddmx = [(identi, '=', p['id']), ('conector', '=', 'linio')]

                    ppt = self.env['product.template'].search(ddmx)
                    if not ppt:
                        datax = {
                            'name': p['title'],
                            'id_vex': p['id'],
                            'list_price': 1,
                            #'server_vex': int(server.id),
                            'conector': server.conector,
                            'type': "product",
                            'categ_id': server.categ_id.id,
                            'active': True,
                            'uom_id': 1,
                            'uom_po_id': 1,
                            'tracking': "none",
                            'sale_line_warn': "no-message",
                            'invoice_policy': "order",
                            'sale_ok': True,
                            'purchase_ok': True ,

                        }
                        if not server.share_multi_instances:
                            datax['server_vex'] = int(server.id)

                        datav = {
                            'model': 'product.template',
                            'data': [datax]
                        }

                        self.env['vex.web.services'].create_update(datav)

                        dddx = [('id_vex', '=', p['id']),('server_vex', '=', int(server.id))]
                        if server.share_multi_instances:
                            dddx = [('id_vex', '=', p['id']), ('conector', '=', str(server.conector))]



                        ppt = self.env['product.template'].search(dddx)





                    datax = {
                        'id_vex_varition': atributo,
                        'product_tmpl_id': ppt.id
                    }

                    pp = self.env['product.product'].create(datax)



                    if not pp:
                        raise ValidationError('queee')

        else:
            try:
                ppt = self.check_produc(p['Sku'],  server , accion)
            except:
                dmx = [('default_code', '=', p['Sku']),('server_vex', '=', int(server.id))]
                ppt = self.env['product.template'].search(dmx)
                #if not ppt:
                #    raise ValueError([dmx,p])
                if not ppt:
                    return None
                    datax = {
                        'name': p['title'],
                        'id_vex': p['id'],
                        'list_price': 1,
                        'server_vex': int(server.id),
                        'conector': server.conector,
                        'type': "product",
                        'categ_id': server.categ_id.id,
                        'active': True,
                        'uom_id': 1,
                        'uom_po_id': 1,
                        'tracking': "none",
                        'sale_line_warn': "no-message",
                        'invoice_policy': "order",
                        'sale_ok': True,
                        'purchase_ok': True}

                    datav = {
                        'model': 'product.template',
                        'data': [datax]
                    }

                    self.env['vex.web.services'].create_update(datav)

                    ppt = self.env['product.template'].search([('id_vex', '=', p['id']),
                                                               ('server_vex', '=', int(server.id))])
                datax = {
                    'product_tmpl_id': ppt.id ,
                    'base_unit_count': 0  ,
                }

                datav = {
                    'model': 'product.product',
                    'data': [datax]
                }

                self.env['vex.web.services'].create_update(datav)


            #raise ValidationError(pt.id_vex)
            #raise ValidationError(pt.product_variant_ids)

            pp = self.env['product.product'].search([('product_tmpl_id', '=', int(ppt.id))])
            #raise ValidationError(pp)


        return  pp


    def insert_lines(self,lines,server,creado , accion):
        if server.conector == 'linio':
            total_base = 0
            total_tax = 0
            total_amount = 0
            order_ids = []
            for p in lines:
                #raise ValidationError(str(p))
                # raise ValidationError(p['quantity'])
                #atributo = p['Variation']]
                existe = self.check_product_order_linio(p, server, accion)

                p_id = existe
                if not p_id:
                    #raise ValidationError('no_producto'+str(p))
                    # no se encontro elproducto por alguna razon
                    # crear producto temporal
                    temp = self.env['product.product'].search([('id_vex_varition', '=', 'tmp')])
                    if not temp:
                        temp = self.env['product.product'].create({
                            'name': 'Producto temporal conector',
                            'id_vex_varition': 'tmp' ,
                            'base_unit_count': 0
                        })
                    p_id = temp

                    start_date = fields.Datetime.now()
                    dx = {
                        'start_date': "'{}'".format(start_date),
                        'end_date': "'{}'".format(start_date),
                        'description': "'Error importing {}  product sku {} : '".format(accion.name, p['ShopSku']),
                        'state': "'error'",
                        'server_vex': server.id,
                        'vex_list': accion.id,
                        'detail': "'Error importing {}  product id {} in order id {} '".format(accion.name,
                                                                                               p['ShopSku'],
                                                                                               creado.id_vex),
                    }

                    self.json_execute_create('vex.logs', dx)

                with_tax = float(p['ItemPrice'])

                #without_tax = with_tax - ((with_tax *  server.tax_id.amount)  / 100)
                without_tax = with_tax - float(p['TaxAmount'])
                #tax = float(p['TaxAmount'])

                tb = without_tax * int(p['IsProcessable'])
                total_base += tb

                ptot =  with_tax * int(p['IsProcessable'])
                total_amount += ptot




                if 1 == 5 :
                    new_line = {
                        # 'name':str(existe.name),
                        'name': "'" + str(p['Name']) + "'",
                        'product_id': p_id.id,
                        'product_uom_qty': int(p['IsProcessable']),
                        'price_unit': without_tax,
                        'price_reduce': without_tax,
                        'price_reduce_taxinc': with_tax,
                        'price_reduce_taxexcl': without_tax,
                        # 'price_unit_with_tax': float(p['ItemPrice']),
                        'order_id': creado.id,
                        'price_subtotal': tb,
                        'price_total': ptot,
                        'price_tax': tax,
                        # campos requeridos
                        'customer_lead': 1.0,
                        'invoice_status': "'no'",
                        'company_id': server.company.id,
                        'currency_id': server.pricelist.currency_id.id,
                        'product_uom': 1,
                        'discount': 0

                    }
                    is_auto_so = self.env['ir.module.module'].search(
                        [('name', '=', 'so_auto_invoice'), ('state', '=', 'installed')])
                    if is_auto_so:
                        new_line['price_unit_with_tax'] = with_tax
                    self.json_execute_create('sale.order.line', new_line)

                #raise ValidationError(str(p))

                new_line = {
                    # 'name':str(existe.name),
                    'name': str(p['Name']) ,
                    'product_id': p_id.id,
                    'product_uom_qty': int(p['IsProcessable']),
                    'price_unit': without_tax,
                    #'price_reduce': without_tax,
                    #'price_reduce_taxinc': with_tax,
                    #'price_reduce_taxexcl': without_tax,
                    # 'price_unit_with_tax': float(p['ItemPrice']),
                    #'order_id': creado.id,
                    #'price_subtotal': tb,
                    #'price_total': ptot,
                    #'price_tax': tax,
                    # campos requeridos
                    #'customer_lead': 1.0,
                    #'invoice_status': "'no'",
                    'company_id': server.company.id,
                    'currency_id': server.pricelist.currency_id.id,
                    #'product_uom': 1,
                    'discount': 0 ,
                    'tax_id': [(6,0,[server.tax_id.id])] if server.tax_id else None ,
                    'linio_order_item_id': str(p['OrderItemId']) ,
                    'linio_shop_id': str(p['ShopId']) ,
                    'linio_shippingtype': p['ShippingType']

                }
                order_ids.append(int(p['OrderItemId']))

                creado.order_line += self.env['sale.order.line'].new(new_line)

                if 'ShippingAmount' in p:
                    ship_amount = float(p['ShippingAmount'])

                    if ship_amount != 0 :
                        envio = self.env['product.product'].search([('id_vex_varition', '=', 'shipping_linio')])
                        if not envio:
                            envio = self.env['product.product'].create({
                                'name': 'Envio Linio',
                                'id_vex_varition': 'shipping_linio',
                                'base_unit_count': 0,
                                'type': 'service',
                                'detailed_type': 'service',
                            })

                        new_line = {
                            # 'name':str(existe.name),
                            'name': envio.name,
                            'product_id': envio.id,
                            'product_uom_qty': 1,
                            'price_unit': ship_amount,
                            # 'price_reduce': without_tax,
                            # 'price_reduce_taxinc': with_tax,
                            # 'price_reduce_taxexcl': without_tax,
                            # 'price_unit_with_tax': float(p['ItemPrice']),
                            # 'order_id': creado.id,
                            # 'price_subtotal': tb,
                            # 'price_total': ptot,
                            # 'price_tax': tax,
                            # campos requeridos
                            # 'customer_lead': 1.0,
                            # 'invoice_status': "'no'",
                            'company_id': server.company.id,
                            'currency_id': server.pricelist.currency_id.id,
                            # 'product_uom': 1,
                            'discount': 0,
                            # 'tax_id': [(6, 0, [server.tax_id.id])] if server.tax_id else None,
                            'tax_id': False,
                            'linio_order_item_id': str(p['OrderItemId']),
                            'linio_shop_id': str(p['ShopId']),
                            'linio_shippingtype': p['ShippingType']

                        }

                        creado.order_line += self.env['sale.order.line'].new(new_line)


                if server.use_warehousetype:
                    if p['ShippingType'] == 'Dropshippingse':
                        creado.warehouse_id = server.warehouse_dropshipping.id
                    if p['ShippingType'] == 'Own Warehouse':
                        creado.warehouse_id = server.warehouse_ownwarehouse.id


                '''
                try:
                    self.json_execute_create('sale.order.line', new_line)
                except:
                    start_date = fields.Datetime.now()
                    dx = {
                        'start_date': "'{}'".format(start_date),
                        'end_date': "'{}'".format(start_date),
                        'description': "'Error creating line order  {}  product id {} : '".format(accion.name,
                                                                                                  p['item']['id']),
                        'state': "'error'",
                        'server_vex': server.id,
                        'vex_list': accion.id,
                        'detail': "'Error creating {}  product id {} in order id {} '".format(accion.name,
                                                                                              p['item']['id'],
                                                                                              p['id']),
                    }

                    self.json_execute_create('vex.logs', dx)
                '''

            return order_ids
        else:
            res = super(LinioActionSynchro, self).insert_lines(lines, server, creado, accion)
            return res


    def start_sync_sale_linio(self):
        #importar solo info de productos
        servers = self.env['vex.instance'].search([('active_automatic', '=', True)])
        #raise ValidationError(servers)
        for s in servers:
            wizard = self.env['vex.synchro'].create(dict(
                server_vex=s.id,
                accion=self.env.ref('linio_connector_vex.linio_action_products', False).id ,
                conector='linio',
                type_log='automatic'

            ))
            #raise ValidationError()
            wizard.start_import()

            wizard = self.env['vex.synchro'].create(dict(
                server_vex=s.id,
                accion=self.env.ref('linio_connector_vex.linio_action_orders', False).id,
                conector='linio',
                type_log='automatic'

            ))
            wizard.start_import()



        #iniciar la importacion de las ventas
        return

    def start_sync_stock_linio(self):
        products = self.env['product.product'].search([('conector','=','linio')],limit=250)
        #,('check_export_linio','!=',True)

        #raise ValidationError(str(products))


        products.update_conector_vex()

        #if products:
        #    self.env.cr.execute(f'''UPDATE product_template SET check_export_linio = 't'  WHERE id in {tuple(products.ids)}''')
        #else:
        #    self.env.cr.execute(f'''UPDATE product_template SET check_export_linio = 'f'  ''')

