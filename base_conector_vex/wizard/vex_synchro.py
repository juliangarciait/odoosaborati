from odoo import api, fields, models
import threading
import requests
# import base64

# from datetime import datetime
# from urllib.parse import urlparse
import logging
# import pprint
import math
# import html2text
# import subprocess
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)
# from difflib import SequenceMatcher
# from datetime import timedelta

import datetime
from datetime import datetime


id_api = "id_vex"
server_api = "server_vex"


class PopupVex(models.TransientModel):
    _name = 'popup.vex'
    _description = 'descripcion'

    name = fields.Char()
    message = fields.Text(string='Resultado: ')

    # output_name = fields.Char(string='Nombre del Archivo')
    # output_file = fields.Binary(string='Archivo', readonly=True, filename="output_name")

    def get_message(self, message):
        wizard = self.create({'name': 'Mensaje', 'message': message})

        return {
            'res_id': wizard.id,
            'view_mode': 'form',
            'res_model': 'popup.vex',
            'views': [[self.env.ref('base_conector_vex.popup_vex_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class WooSynchro(models.TransientModel):
    _name = "vex.synchro"
    _description = "Synchronized server Vex"
    # server             = fields.Many2one('woo.synchro.server', "Server ", required=True)
    accion = fields.Many2one('vex.restapi.list', required=True)
    current_pag = fields.Integer()
    total_paginaciones = fields.Integer()
    argument = fields.Char(related="accion.argument")
    import_unit = fields.Boolean()
    id_vex = fields.Char(string='Id Connector')
    server_vex = fields.Many2one('vex.instance', 'Instance')
    conector = fields.Char()
    stock_import = fields.Boolean()
    import_images = fields.Boolean()
    import_images_website = fields.Selection([('save', 'Save url'), ('dowload', 'Save url and Dowload')])
    type_log = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatico')],default='manual',required=True)

    @api.model
    def start_sync_automatic(self):
        # buscar el modelo del cron automatico
        cron = self.env.ref('base_conector_vex.vex_soluciones_ir_cron_automatico', False)
        # raise ValidationError(cron)
        if cron:
            servers = self.env['vex.instance'].search([('active_automatic', '=', True)])
            for s in servers:
                # s.active_automatic = True
                # raise ValidationError('ohh')
                self.check_synchronize(s)
                self.synchronize(s.active_list, s, None)


    def get_total_data_count(self):
        return 0

    def get_total_count(self):
        return 0

    def import_all(self, server, accion, query=''):
        return query

    def import_by_parts(self, server, accion, query):
        return 0

    def get_data_id(self, id_vex, server, query):
        return 0

    def synchro_unit_wizard(self):
        if self.argument == 'products':
            self.accion.stock_import = self.stock_import
            self.accion.import_images = self.import_images
            self.accion.import_images_website = self.import_images_website
        self.synchro_unit(self.accion, self.accion.model, self.server_vex, self.id_vex)

    def synchro_unit(self, accion, model, server_vex, id_vex, api=None):
        self.check_synchronize(server_vex)
        item = self.get_data_id(id_vex, server_vex, accion.argument)

        self.synchro(item, accion.argument, server_vex, model, accion, id_vex, None)

        if model == 'product.template' and accion.stock_import:
            products = []
            pro = self.env['product.template'].search(
                [('id_vex', '=', str(id_vex)), ('server_vex', '=', server_vex.id)])
            products.append(pro)
            self.import_stock(server_vex, products)
        # raise ValidationError(query)

    def json_execute_create(self, table, data, return_query=False):
        table = str(table).replace('.', '_')
        filas_create = ''
        values_create = ''
        if table == 'product_template':
            data['active'] = "'t'"
            data['uom_id'] = 1
            data['uom_po_id'] = 1
            data['tracking'] = "'none'"
            data['sale_line_warn'] = "'no-message'"
            data['invoice_policy'] = "'order'"
            data['sale_ok'] = "'t'"
            data['purchase_ok'] = "'t'"
        for d in data:
            filas_create = filas_create + ', ' + str(d)
            values_create = values_create + ', ' + str(data[d])
        filas_create = filas_create[1:]
        values_create = values_create[1:]
        create = "INSERT INTO  {tabla} ({filas}) VALUES ({values}) ; \n".format(tabla=table,
                                                                                filas=filas_create,
                                                                                values=values_create)
        if return_query:
            return create
        self.env.cr.execute(create)

    def json_execute_update(self, table, data, id_vex, return_query=False):
        table = str(table).replace('.', '_')
        set_update = ''
        for d in data:
            set_update = set_update + ', ' + str(d) + '=' + str(data[d])
        set_update = set_update[1:]
        write = "UPDATE {tabla} set {set} where id = {id_vex} ; \n ".format(tabla=table, set=set_update, id_vex=id_vex)
        if return_query:
            return write
        self.env.cr.execute(write)

    def sql_fields(self, table, data, id_vex, api):
        # table = accion.model
        table = str(table).replace('.', '_')
        filas_create = ''
        values_create = ''
        set_update = ''
        if 'create' in data:
            # campos obligatorios
            # self.json_execute_create(table,data['create'])

            if table == 'product_template':
                data['create']['active'] = "'t'"
                data['create']['uom_id'] = 1
                data['create']['uom_po_id'] = 1
                data['create']['tracking'] = "'none'"
                data['create']['sale_line_warn'] = "'no-message'"
                data['create']['invoice_policy'] = "'order'"
                data['create']['sale_ok'] = "'t'"
                data['create']['purchase_ok'] = "'t'"
            for d in data['create']:
                filas_create = filas_create + ', ' + str(d)
                values_create = values_create + ', ' + str(data['create'][d])
            filas_create = filas_create[1:]
            values_create = values_create[1:]

        if 'write' in data:

            if table == 'product_template':
                data['write']['active'] = "'t'"
                data['write']['uom_id'] = 1
                data['write']['uom_po_id'] = 1
                data['write']['tracking'] = "'none'"
                data['write']['sale_line_warn'] = "'no-message'"
                data['write']['invoice_policy'] = "'order'"
                data['write']['sale_ok'] = "'t'"
                data['write']['purchase_ok'] = "'t'"
            for d in data['write']:
                set_update = set_update + ', ' + str(d) + ' = ' + str(data['write'][d])
            set_update = set_update[1:]

        create = "INSERT INTO  {tabla} ({filas}) VALUES ({values}) ; \n".format(tabla=table,
                                                                                                       filas=filas_create,
                                                                                                       values=values_create)
        #ON CONFLICT DO NOTHING

        write = "UPDATE {tabla} SET {set} WHERE id_vex = '{id_vex}' ; \n".format(tabla=table, set=set_update,
                                                                                 id_vex=id_vex)

        return {
            'create': create,
            'write': write,

        }

    def json_fields(self, data, query, server,accion=None):
        create = {}
        write = {}
        if query == "products":

            # verificar si el modulo compras esta istalado
            is_purchase = self.env['ir.module.module'].search([('name', '=', 'purchase'), ('state', '=', 'installed')])
            if is_purchase:
                create['purchase_line_warn'] = "'no-message'"

            if not server.categ_id:
                raise ValidationError("instance, products' category not indicated")

            if not server.share_multi_instances:
                create['server_vex'] = server.id

        if query == 'orders':
            salesteam = server.sales_team
            create['team_id'] = salesteam.id
            create['user_id']: server.user_sale_id.id if server.user_sale_id else None
            if server.medium_id:
                create['medium_id'] = server.medium_id.id

        return {
            'create': create,
            'write': write,
        }

    def import_stock(self, server, products):

        if not server.location_id:
            raise ValidationError('Debe Indicar una Localizaion')
        location = server.location_id
        variantes = self.env['product.product'].search([('product_tmpl_id', 'in', products.ids)])

        for p in variantes:
            quantun = self.env['stock.quant'].search([('product_id', '=', p.id), ('location_id', '=', location.id)])
            if not quantun:
                quantun = self.env['stock.quant'].sudo().create(
                    dict(
                        product_id=p.id,
                        location_id=location.id,
                        inventory_quantity=p.stock_vex,
                    )
                )
            else:
                quantun.sudo().inventory_quantity = p.stock_vex
            quantun.sudo()._apply_inventory()

    def insert_lines_stock(self, l, variante, inventory):

        invline = self.env['stock.inventory.line'].search(
            [('product_id', '=', int(variante.id)), ('inventory_id', '=', int(inventory.id))])
        if not invline:
            self.env['stock.inventory.line'].create({
                'product_id': variante.id,
                'product_qty': variante.stock_vex,
                'location_id': inventory.location_ids[0].id,
                'inventory_id': inventory.id,
                'product_uom_id': variante.uom_id.id,
                'company_id': inventory.company_id.id,
            })
        else:
            invline.write({
                'product_qty': variante.stock_vex
            })

        return 0

    def synchro_ext(self, data, query, server, table, accion, id_vex, api, exist, queryx='', is_exist_sku=False):
        if query == 'orders':

            if not exist.create_date or exist.create_date == False:
                create_date = exist.date_order.date()
                query = f'''UPDATE sale_order SET create_date = '{str(create_date)}' WHERE id = {exist.id}'''
                self.env.cr.execute(query)

            if not exist.team_id:
                exist.team_id = server.sales_team.id
            if not exist.user_id:
                exist.user_id = server.user_sale_id.id

            if not exist.medium_id and server.medium_id:
                exist.medium_id =  server.medium_id.id


        return queryx

    def synchro_threading(self, data, query, server, table, accion, id_vex, api):
        th = []
        for dr in data:
            threaded_synchronization = threading.Thread(
                target=self.except_synchro(dr, query, server, table, accion, id_vex, api))
            # threaded_synchronization = threading.Thread(self.except_synchro(m, accion, wcapi, server, table, fast))
            th.append(threaded_synchronization)
        for t in th:
            t.run()

        return 0

    def except_synchro(self, data, query, server, table, accion, id_vex, api=None):
        self.synchro(data, query, server, table, accion, id_vex, api)
        '''
        try:
            self.synchro(data, query, server, table, accion,id_vex ,api)

        except:
            start_date = fields.Datetime.now()
            dx = {
                'start_date': "'{}'".format(start_date),
                'end_date': "'{}'".format(start_date),
                'description': "'Error importing {}  id {} : '".format(accion.name,data['body']['id'] if 'body' in data else data['id']),
                'state': "'error'",
                'server_vex': server.id,
                'vex_list': accion.id,
                #'conector': "{}".accion.conector
            }
            self.json_execute_create('vex.logs',dx)
        '''

    @api.model
    def synchro(self, data, query, server, table, accion, id_vex, api=None, queryx='',default_code=None):
        #raise ValidationError(str(data))
        conector = server.conector

        data_json = self.json_fields(data, query, server)
        # raise ValidationError(id_vex)
        sql_fields = self.sql_fields(table, data_json, id_vex, api)
        # import json

        is_exist_sku = False

        #domain origin

        domain = [('id_vex', '=', str(id_vex)), ('server_vex', '=', int(server.id))]
        # ('conector', '=', conector),
        if query == "products":
            if server.share_multi_instances:
                domain = [('id_vex', '=', str(id_vex)), ('conector', '=', str(server.conector))]

            if server.search_archive_products:
                domain = domain + ['|', ('active', '=', True), ('active', '=', False)]


        if query == "orders":
            domain = [('id_vex', '=', str(id_vex)),
                      ('server_vex', '=', int(server.id)), ('primary_order_id', '=', False)]

        if 'domain' in data:
            domain = data['domain']

        exist = self.env[table].search(domain)

        if server.search_sku and query == 'products' and 'default_code' in data_json['create'] and  (not exist or len(exist) > 1):

            if not default_code:
                raise ValidationError(str(data_json['create']))
            #

            # or data_json['create']['default_code']
            domain = [('default_code', '=', default_code.strip())]
            exist = self.env[table].search(domain)

        #search if exist the variant sku




        if server.search_sku and query == 'products' and 'default_code' in data_json['create'] and (not exist or len(exist) > 1):
            exist_product = self.env['product.product'].search(domain)

            contador_existentes = 0

            if  exist_product:
                if len(exist_product) > 1 :
                    for product_searched in exist_product:

                        if product_searched.product_tmpl_id.conector and product_searched.product_tmpl_id.id_vex:
                            try:
                                product_searched.product_tmpl_id.id_vex = product_searched.product_tmpl_id.id_vex+'_old'

                                product_searched.default_code = product_searched.default_code + '_old'
                            except:
                                raise ValidationError(str(['cambiando', product_searched.product_tmpl_id.conector , product_searched.id ,exist_product, id_vex, data,]))

                            start_date = fields.Datetime.now()
                            product_searched.product_tmpl_id.conector = False

                            dx = {
                                'start_date': "'{}'".format(start_date),
                                'end_date': "'{}'".format(start_date),
                                'description': f"'producto modificado : {product_searched.display_name} , id:  {product_searched.id} , sku : {id_vex} '",
                                'state': "'done'",
                                'server_vex': server.id,
                                'vex_list': accion.id,
                                'type': "'{}'".format(self.type_log),
                                # 'conector': "{}".accion.conector
                            }
                            self.json_execute_create('vex.logs', dx)

                        else:
                            if contador_existentes > 1:
                                raise ValidationError(f'''se encontro mas de un existe variant {str(exist_product)} , {id_vex}''')
                            exist = product_searched.product_tmpl_id
                            exist.conector = conector
                            product_searched.id_vex_varition = str(id_vex)
                            contador_existentes += 1
                if contador_existentes == 1 :
                    #raise ValidationError(str([exist_product, id_vex, data]))
                    return queryx
                if len(exist_product) == 1 :
                    if not exist_product.id_vex_varition and len(exist_product.product_tmpl_id.product_variant_ids) > 1:
                        if not exist_product.conector:
                            exist = exist_product.product_tmpl_id
                            exist.conector = conector
                            #product_searched.id_vex_varition = str(id_vex)
                            #raise ValidationError(f'''NO ESTA MACHEADO {exist_product.display_name}''')
                        exist_product.id_vex_varition = str(id_vex)
                    return queryx
            #raise ValidationError(str([exist_product,domain,exist]))

            #if id_vex == '120021':
            #    raise ValidationError(str([id_vex,exist_product]))

        has_create = False

        if not exist:
            self.env.cr.execute(sql_fields['create'])
            has_create = True
            '''

            try:
                self.env.cr.execute(sql_fields['create'])
            except:
                raise ValidationError(sql_fields['create'])
            '''
        
            #raise ValidationError(exist)
        else:
            # raise ValidationError(sql_fields['write'])
            # queryx += sql_fields['write']
            if server.search_sku and query == 'products' and default_code:
                is_exist_sku = True
                #write = {
                #    'conector': f"'{conector}'",
                #    'server_vex': server.id,
                #    'id_vex': "'" + str(id_vex) + "'",
                #}
                tablec = str(table).replace('.', '_')
                add_id_server = f''', server_vex = {server.id}'''
                if server.share_multi_instances:
                    add_id_server = ''

                if len(exist) > 1:
                    raise ValueError([exist,domain])

                query_updatex = f"UPDATE {tablec} SET  conector = '{conector}' , id_vex = '{str(id_vex)}' {add_id_server}  WHERE default_code = '{default_code}' ;"
                query_updatex += f"UPDATE product_product SET id_vex_varition = '{str(id_vex)}' , base_unit_count = 0 WHERE product_tmpl_id = {exist.id} ;"
                sql_fields['write'] =  query_updatex



            # ValueError([sql_fields['write'],data_json])
            #raise ValidationError(data_json)
            if data_json['write']:
                self.env.cr.execute(sql_fields['write'])
            #try:
            #    if data_json['write']:
            #        self.env.cr.execute(sql_fields['write'])

            #except:
            #    raise ValidationError(sql_fields['write'])


            # raise ValidationError('escribir')

        #if conector == 'meli':
        #    domain = [('id_vex', '=', str(id_vex)), ('conector', '=', str(server.conector))]

        exist = self.env[table].search(domain)

        if not exist:
            exist_product = self.env['product.product'].search(domain)



            raise ValidationError(str([server.search_sku,data_json['create'],exist,exist_product.default_code,id_vex,default_code]))
            raise ValidationError('no se encontro' + str(exist) + ':' + str(table) + ',' + str(domain)+'/'+str(sql_fields['create']))


        if has_create:
            self.execute_after_create(data, query, server, table, accion, id_vex, api, exist,queryx ,is_exist_sku)

        queryx += self.synchro_ext(data, query, server, table, accion, id_vex, api, exist,queryx ,is_exist_sku)
        return queryx

    def execute_after_create(self,data, query, server, table, accion, id_vex, api, exist,queryx ,is_exist_sku):
        return

    def synchronize(self, accion, server, bypart=False):
        server.validate_licence()
        # raise ValidationError('holaa')
        table = str(accion.model)
        query = str(accion.argument)
        rango = int(accion.per_page)
        # pag = self.get_pages(server, accion)
        current_page = 0
        ####
        total_data_count = 0
        total_pag = 0
        finish_loop = False
        start_date = fields.Datetime.now()
        if accion.import_by_parts or bypart:
            # raise ValidationError('por partes')
            # self.import_by_parts()
            # total_data_count = self.get_total_data_count()
            # total_pag = math.ceil(total_data_count / rango)

            # current_page = int(pag['current']) + 1
            finish_loop = self.import_by_parts(server, accion, accion)
        else:
            # raise ValidationError('Total')
            # tt = self.get_total_count()
            # raise ValidationError(tt)
            # total_pag = tt
            # current_page = tt
            finish_loop = self.import_all(server, accion)

        end_date = fields.Datetime.now()
        dx = {
            'start_date': "'{}'".format(start_date),
            'end_date': "'{}'".format(end_date),
            'description': "'{}  successfully synchro   '".format(accion.name),
            'state': "'done'",
            'server_vex': server.id,
            'vex_list': accion.id,
            'type': "'{}'".format(self.type_log),
            # 'conector': "{}".accion.conector
        }
        self.json_execute_create('vex.logs', dx)
        # raise ValidationError('hols')

        return finish_loop

        '''
        if int(pag['current']) >= total_pag:
            return {
                'current': 0,
                'total': 0
            }
        return {
            'current': current_page,
            'total': total_pag
        }
        '''

    def get_pages(self, server, accionx):
        accion = self.env['vex.logs'].search([('server_vex', '=', server.id),
                                              ('state', '=', 'done'), ('stock', '=', False), ('webhook', '=', False),
                                              ('vex_list', '=', accionx.id)],
                                             order="id desc", limit=1)
        if accion:
            if int(accion.page) >= int(accion.total):
                tt = 0
            else:
                tt = int(accion.page)
        else:
            tt = 0
        return {
            'current': tt,
            'total': int(accion.total)
        }

    def check_synchronize(self, server):
        return 0

    def start_import(self):
        if self.argument == 'products':
            self.accion.stock_import = self.stock_import
            self.accion.import_images = self.import_images
            self.accion.import_images_website = self.import_images_website
        return 0

    def vex_import(self, id_action, wcapi=None):
        # get instance selected
        server = self.server_vex
        # check tokens access
        self.check_synchronize(server)
        accion = self.accion
        finish_loop = False
        '''
        a = 0
        while finish_loop == False:
            #raise ValidationError('kkk')
            finish_loop = self.synchronize(accion, server, wcapi)
            a += 1
            if a >10:
                raise ValidationError('heuu')
        '''
        self.synchronize(accion, server, wcapi)
        # raise ValidationError(finish_loop)
        # pag = self.get_pages(server, self.accion)
        pag = {'current': 0}
        if int(pag['current']) == 0:
            view_rec = self.env.ref('base_conector_vex.vex_import_synchro_finish',
                                    raise_if_not_found=False)
        else:
            view_rec = self.env.ref('base_conector_vex.vex_import_synchro_finish_cron',
                                    raise_if_not_found=False)
        # raise ValidationError(id_action)
        action = self.env.ref(
            id_action, raise_if_not_found=False
        ).read([])[0]
        action['views'] = [(view_rec and view_rec.id or False, 'form')]
        # action['target'] = 'new'
        return action

    def check_customer(self, dt, server, customer_id, accion):
        data = dt
        #raise ValidationError(str(dt))
        #data['customer'] = dt['customer']
        data['customer']['id_vex'] = str(customer_id)
        #data['customer']['server_vex'] = server.id
        data['customer']['conector'] = "{}".format(server.conector)
        data['customer']['active'] = True
        if server.type_document:
            data['customer']['l10n_latam_identification_type_id'] = server.type_document.id

        billing, shipping, partner = None, None, None
        if customer_id != 0 or customer_id != None:
            # buscar la data del cliente en woocomerce
            # pr = wcapi.get("customers/" + str(customer_id)).json()
            # buscar el cliente en res.partner odoo
            #dmm = [('id_vex', '=', str(customer_id)), ('server_vex', '=', int(server.id))]
            dmm = [('id_vex', '=', str(customer_id)),'|',('active','=',True),('active','=',False)]
            partner = self.env['res.partner'].search(dmm)
            if not partner:
                #if data['customer']['id_vex'] == '544056182':
                #    raise ValidationError(str([dmm]))
                if 'billing' in data:
                    data['customer']['street'] = data['billing']['street']
                    '''
                    billing = self.env['res.partner'].search([('parent_id', '=', partner.id), ('type', '=', 'invoice')],
                                                             limit=1)
                    if not billing:
                        bi = data['billing']
                        bi['parent_id'] = partner.id
                        bi['type'] = "'invoice'"
                        bi['id_vex_parent'] = f"'{partner.id_vex}'"
                        bi['active'] = "'t'"
                        # jsonc = self.json_fields(bi, 'customers', wcapi, server)
                        # query_customer = "INSERT INTO res_partner ()"
                        # billing = self.env['res.partner'].create(jsonc['create'])
                        self.json_execute_create('res.partner',bi)
                        billing =  self.env['res.partner'].search([('type','=','invoice'),('parent_id', '=', int(partner.id))])
                    '''

                #self.json_execute_create('res.partner', data['customer'])
                try:
                    partner = self.env['res.partner'].create(data['customer'])
                except:
                    partner = self.env['res.partner'].search(dmm)
                    raise ValueError(str([partner,data['customer']]))

                #dmx = [('id_vex', '=', str(customer_id)), ('server_vex', '=', int(server.id))]
                #dmx = [('id_vex', '=', str(customer_id))]
                #partner = self.env['res.partner'].search(dmx)

                #desactivado #activar si pidem
                '''
                if 'shipping' in data:
                    shipping = self.env['res.partner'].search(
                        [('parent_id', '=', partner.id), ('type', '=', 'delivery')])
                    if not shipping:

                        # crear para envio envio
                        sh = data['shipping']
                        sh['parent_id'] = partner.id
                        sh['type'] = "delivery"
                        sh['id_vex_parent'] = partner.id_vex
                        sh['active'] = True
                        shipping = self.env['res.partner'].create(sh)
                        #self.json_execute_create('res.partner',sh)
                        #shipping = self.env['res.partner'].search([('type','=','delivery'),('parent_id', '=', int(partner.id))])
                '''

        else:
            partner = self.env['res.partner'].create(data['customer'])
            #partner = self.json_execute_create('res.partner', data['customer'])
            '''
            # datos para la facturacion
            billing = data['billing']
            # datos para el envio
            shipping = data['shipping']
            # country = self.get_country(billing['country'])
            # state   = self.get_state(country ,billing['state'])
            partner = self.env['res.partner'].create({
                'name': str(data['billing']['first_name']) + " " + str(data['billing']['last_name']),
                'woo_first_name': str(data['billing']['first_name']),
                'woo_last_name': str(data['billing']['last_name']),
                'phone': str(data['billing']['phone']),
                'email': data['billing']['email'],
                'property_product_pricelist': server.pricelist.id,
                'server': server.id,
                'orden_woo_id': data['id']
            })

            bi = data['billing']
            bi['parent_id'] = partner.id
            bi['type'] = 'invoice'
            bi['id_woo_parent'] = partner.id_woo
            jsonc = self.json_fields(bi, 'customers', wcapi, server)
            billing = self.env['res.partner'].create(jsonc['create'])

            sh = data['shipping']
            sh['parent_id'] = partner.id
            sh['type'] = 'delivery'
            sh['id_woo_parent'] = partner.id_woo
            jsons = self.json_fields(sh, 'customers', wcapi, server)
            shipping = self.env['res.partner'].create(jsons['create'])
            '''

        return {
            'customer': partner,
            'invoice': billing if billing else partner,
            'shipping': shipping if shipping else partner
        }

    def insert_fee_lines(self, fee_lines, creado, server, key, key_total, sg):
        total_fee = 0
        if fee_lines:
            for f in fee_lines:
                iw = f[key]
                tfe = float(f[key_total] * sg)


                total_fee += float(f[key_total] * sg) * f['quantity']

                if tfe and server.discount_fee == 'save_line':


                    ppf = self.env['product.template'].search([('server_vex', '=', server.id), ('id_vex', '=', iw)])

                    if not ppf:
                        crea = {
                            'name': "'fee_" + str(iw) + "'",
                            'id_vex': "'" + str(iw) + "'",
                            'list_price': float(f[key_total] * sg),
                            'server_vex': server.id,
                            'type': "'service'",
                            'conector': "'" + str(server.conector) + "'",
                            'categ_id': server.categ_id.id,
                            #'base_line_count': 0 ,
                            'sale_line_warn': "'no-message'",
                            'detailed_type': "'service'" ,
                            'base_unit_count': 0

                        }
                        # verificar si el modulo compras esta istalado
                        is_purchase = self.env['ir.module.module'].search(
                            [('name', '=', 'purchase'), ('state', '=', 'installed')])
                        if is_purchase:
                            crea['purchase_line_warn'] = "'no-message'"
                        self.json_execute_create('product.template', crea)
                    ppf = self.env['product.template'].search([('server_vex', '=', server.id), ('id_vex', '=', iw)])
                    # raise ValidationError(ppf)
                    pp = self.env['product.product'].search(
                        [('server_vex', '=', server.id), ('product_tmpl_id', '=', ppf.id)])
                    if not pp:
                        crea = {
                            'product_tmpl_id': ppf.id,
                            'active': "'t'" ,
                            'base_unit_count': 0,
                        }
                        self.json_execute_create('product.product', crea)
                    pp = self.env['product.product'].search([('product_tmpl_id', '=', ppf.id)], limit=1)

                    #raise   ValidationError(str(f))
                    # raise ValidationError(pp)

                    new_line = {
                        # 'name':str(existe.name),
                        'name': "'" + str(pp.name) + "'",
                        'product_id': pp.id,
                        'product_uom_qty': f['quantity'],
                        'price_unit': float(f[key_total] * sg) * f['quantity'] ,
                        #'price_reduce': float(f[key_total] * sg),
                        #'price_reduce_taxinc': float(f[key_total] * sg),
                        #'price_reduce_taxexcl': float(f[key_total] * sg),
                        'order_id': creado.id,
                        #'price_subtotal': float(f[key_total] * sg),
                        #'price_total': float(f[key_total] * sg),
                        #'price_tax': 0.0,
                        # campos requeridos
                        #'customer_lead': 1.0,
                        #'invoice_status': "'no'",
                        'company_id': server.company.id,
                        'currency_id': server.pricelist.currency_id.id,
                        'product_uom': 1,
                        'discount': 0

                    }
                    self.env['sale.order.line'].create(new_line)

                    #self.json_execute_create('sale.order.line', new_line)

        if server.discount_fee == 'save':
            creado.fee_vex = total_fee

        return total_fee

    def insert_lines(self, lines, server, creado, accion):

        for p in lines:
            # raise ValidationError(p['quantity'])
            existe = self.check_product_order(p['item'], server, accion)

            p_id = existe.id
            if not p_id:

                # no se encontro elproducto por alguna razon
                # crear producto temporal
                temp = self.env['product.product'].search([('id_vex_varition', '=', 'tmp')])
                if not temp:
                    temp = self.env['product.product'].create({
                        'name': 'Producto temporal conector',
                        'id_vex_varition': 'tmp' ,
                        'base_unit_count': 0,
                        'type': 'product' ,
                        'detailed_type': 'product' ,

                    })
                p_id = temp.id

                start_date = fields.Datetime.now()
                dx = {
                    'start_date': "'{}'".format(start_date),
                    'end_date': "'{}'".format(start_date),
                    'description': "'Error importing {}  product id {} : '".format(accion.name, p['item']['id']),
                    'state': "'error'",
                    'server_vex': server.id,
                    'vex_list': accion.id,
                    'detail': "'Error importing {}  product id {} in order id {} '".format(accion.name, p['item']['id'],
                                                                                           creado.id_vex),
                }

                self.json_execute_create('vex.logs', dx)

            #raise ValidationError(str(p))

            price_unit = float(p['unit_price'])


            tax_product = server.tax_id
            if server.use_tax_product:
                tax_product = existe.taxes_id
                if tax_product:
                    if len(tax_product) > 1:
                        raise ValidationError('EL PRODUCTO TIENE MAS DE UN IMPUESTO')

            if tax_product:
                if  tax_product.amount != 0 :
                    with_tax = float(p['unit_price'])
                    without_tax = (100 * with_tax) / (100 + tax_product.amount)
                    price_unit = without_tax


                #raise ValidationError(str([p['unit_price'],tax_amount,price_unit,creado.id_vex]))

            new_line = {
                # 'name':str(existe.name),
                'name': "'" + str(p['item']['title']) + "'",
                'product_id': p_id,
                'product_uom_qty': int(p['quantity']),
                'price_unit': price_unit,
                #'price_reduce': float(p['unit_price']),
                #'price_reduce_taxinc': float(p['unit_price']),
                #'price_reduce_taxexcl': float(p['unit_price']),
                'order_id': creado.id,
                #'price_subtotal': float(p['unit_price']) * int(p['quantity']),
                #'price_total': float(p['unit_price']) * int(p['quantity']),
                #'price_tax': 0.0,
                # campos requeridos
                'customer_lead': 1.0,
                #'invoice_status': "'no'",
                'company_id': server.company.id,
                'currency_id': server.pricelist.currency_id.id,
                'product_uom': 1,
                #'discount': 0

            }
            if tax_product:
                new_line['tax_id'] = [(6,0,[tax_product.id])]


            self.env['sale.order.line'].create(new_line)

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
                    'detail': "'Error creating {}  product id {} in order id {} '".format(accion.name, p['item']['id'],
                                                                                          p['id']),
                }

                self.json_execute_create('vex.logs', dx)
            '''

    def check_product_order(self, p, server, accion):




        #raise ValidationError(str(p))
        pp = None
        atributo = p['variation_id']
        # condicion para verificar si es un atributo
        if atributo:
            #raise ValidationError('okk2')

            # buscar en product product
            pp = self.env['product.product'].search(
                [('id_vex_varition', '=', int(atributo)), ('server_vex', '=', int(server.id)), ])
            # si no existe crearlo
            if not pp:

                try:
                    self.check_produc(p['id'], server, accion)
                    pp = self.env['product.product'].search([('id_vex_varition', '=', str(atributo)),
                                                             ('conector', '=', server.conector)])
                    if not pp:
                        raise ValueError('EMPTY DATA')
                except:
                    # crear producto

                    ppt = self.env['product.template'].search([('id_vex', '=', p['id']),
                                                               ('conector', '=', server.conector)])
                    if not ppt:
                        if not server.categ_id:
                            raise ValidationError('not indicate category product')
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
                            'purchase_ok': True ,
                            'detailed_type': "product",
                            'base_unit_count': 0,
                        }

                        # verificar si el modulo compras esta istalado
                        is_purchase = self.env['ir.module.module'].search(
                            [('name', '=', 'purchase'), ('state', '=', 'installed')])
                        if is_purchase:
                            datax['purchase_line_warn'] = "no-message"

                        datav = {
                            'model': 'product.template',
                            'data': [datax]
                        }


                        self.env['vex.web.services'].create_update(datav)

                        ppt = self.env['product.template'].search([('id_vex', '=', p['id']),
                                                                   ('server_vex', '=', int(server.id))])

                    datax = {
                        'id_vex_varition': atributo,
                        'product_tmpl_id': ppt.id ,
                        'base_unit_count': 0

                    }


                    pp = self.env['product.product'].create(datax)

                    if not pp:
                        raise ValidationError('queee')


        else:
            if server.search_sku and p['seller_sku']:
                pp = self.env['product.product'].search([('default_code','=',p['seller_sku'])])
                if not pp:
                    ppt = self.env['product.template'].search([('default_code', '=', p['seller_sku'])])
                    pp = self.env['product.product'].search([('product_tmpl_id', '=', int(ppt.id))])
                    #if not pp:
                    #    raise ValidationError(f'''no se encontro el prodto con el sku {p['seller_sku']}  {str(p)}''')
                #raise ValidationError(str(p))
                #return
            else:

                ppt = self.check_produc(p['id'], server, accion)


                pp = self.env['product.product'].search([('product_tmpl_id', '=', int(ppt.id))])



            #raise ValidationError(ppt)
            '''
            #raise ValidationError('okk')
            try:
                ppt = self.check_produc(p['id'], server, accion)
            except:
                ppt = self.env['product.template'].search([('id_vex', '=', p['id']),
                                                           ('server_vex', '=', int(server.id))])


                if not server.categ_id:
                    raise ValidationError('not indicate category product')
                if not ppt:
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
                        'purchase_ok': True ,
                        'base_unit_count': 0,
                        'detailed_type':  "product"
                    }
                    # verificar si el modulo compras esta istalado
                    is_purchase = self.env['ir.module.module'].search(
                        [('name', '=', 'purchase'), ('state', '=', 'installed')])
                    if is_purchase:
                        datax['purchase_line_warn'] = "no-message"

                    datav = {
                        'model': 'product.template',
                        'data': [datax]
                    }

                    self.env['vex.web.services'].create_update(datav)

                    ppt = self.env['product.template'].search([('id_vex', '=', p['id']),
                                                               ('server_vex', '=', int(server.id))])
                datax = {
                    'product_tmpl_id': ppt.id ,
                    'base_unit_count': 0,
                }

                datav = {
                    'model': 'product.product',
                    'data': [datax]
                }

                #self.json_execute_create('product.product', datav)

                self.env['vex.web.services'].create_update(datav)
                '''

            # raise ValidationError(pt.id_vex)
            # raise ValidationError(pt.product_variant_ids)


            #raise ValidationError(pp)

        return pp

    def check_produc(self, id, server, accion):
        pro_id = None
        dmx = [(id_api, '=', str(id)), (server_api, '=', int(server.id))]
        if server.share_multi_instances:
            dmx = [('conector', '=', str(server.conector)),'|',('id_vex_varition','=',str(id)),(id_api, '=', str(id))]

        existe = self.env['product.product'].search(dmx)
        # raise ValidationError(existe)
        if existe:
            pro_id = existe
        else:
            self.synchro_unit(accion, 'product.template', server, id)
            # raise ValidationError('no existe')
            pro_id = self.env['product.template'].search([(id_api, '=', str(id)), (server_api, '=', int(server.id))])
        return pro_id

    def check_produc_sku(self, id, server, accion):
        #raise ValidationError('llega qui')
        pro_id = None
        dmx = [('default_code', '=', str(id))]
        #, (server_api, '=', int(server.id)
        if server.share_multi_instances:
            dmx = [('default_code', '=', str(id)), ('conector', '=', str(server.conector))]

        existe = self.env['product.template'].search(dmx)
        # raise ValidationError(existe)
        if existe:
            pro_id = existe
        else:
            return None
            self.synchro_unit(accion, 'product.template', server, id)
            # raise ValidationError('no existe')
            pro_id = self.env['product.template'].search(
                [('default_code', '=', str(id)), (server_api, '=', int(server.id))])
        return pro_id



    def get_data_init(self, server, accion, query):

        return {}

    def vex_api(self, server, query, accion, filtro):
        # variable findish loop
        finish_loop = False
        # si es un producto
        if query == "products":
            # verificar si hay lineas esperando

            lines_wait = self.env['vexlines.import'].search([('accion', '=', accion.id),
                                                             ('instance', '=', server.id),
                                                             ('instance', '=', server.id), ('state', '=', 'wait')],
                                                            limit=1)
            # si no hay lineas esperando
            if not lines_wait:
                lw = self.env['vexlines.import'].search([('accion', '=', accion.id),
                                                         ('instance', '=', server.id),
                                                         ('instance', '=', server.id), ('state', '=', 'done')],
                                                        limit=1)
                # 3liminar las lineas finalizadas
                if lw:
                    finish_loop = True
                    self.env['vexlines.import'].search(
                        [('accion', '=', accion.id), ('instance', '=', server.id)]).unlink()
                # update_cron = "UPDATE ir_cron SET active = 'f'  WHERE argument = 'vex_cron' ".format(server.id)
                # self.env.cr.execute(update_cron)

            array_products = []

            # si hay lineas esperando
            if lines_wait:
                # raise ValidationError(lines_wait)
                item_str = lines_wait.url

                res = item_str.split(',')
                # raise ValidationError(res)

                lines_wait.state = 'done'

            else:

                array_products = self.get_data_init(server, accion, query)
                # meli
                '''
                
                API_URL = ''
                products_url = '{}/users/{}/items/search?search_type=scan&access_token={}'.format(API_URL,
                                                                                              str(server.user_id),
                                                                                              str(server.access_token))
                res = requests.get(products_url).json()
                self.insert_import_lines(server,accion,products_url,res)
                res = res[filtro]
                '''
            '''
            for r in res:
                #raise ValidationError(str(r))
                item = self.get_data_init(server,accion,query)
                array_products.append(item)
            '''

            # string_items = ','.join(res)
            # item_url = '{}/items?ids={}&access_token={}'.format(API_URL,string_items,server.access_token)
            # raise ValidationError(item_url)
            # items = requests.get(item_url).json()

            return {
                'data': array_products,
                'finish_loop': finish_loop
            }
        if query == 'categories':
            return {
                'data': self.get_data_init(server, accion, query),
                'finish_loop': finish_loop
            }
        if query == "orders":
            return {
                'data': self.get_data_init(server, accion, query),
                'finish_loop': finish_loop
            }

    @api.model
    def check_terminos(self, t, server, atr, creado=None):

        # sincronizar todos los terminos
        # buscar el id  del termino
        t_id = None
        existe = self.env['product.attribute.value'].search(
            [('name', '=', str(t)), (server_api, '=', int(server.id)), ('attribute_id', '=', int(atr.id))])
        if existe:
            t_id = existe

        return t_id

    @api.model
    def inser_terminos(self, term, atributo, server):
        # import json
        # y = json.dumps(term)
        for t in term:
            et = self.env['product.attribute.value'].search([('name', '=', str(t['name'])),
                                                             (server_api, '=', server.id),
                                                             ('attribute_id', '=', atributo.id)])
            if not et:
                data = {
                    'name': "'" + str(t['name']) + "'",
                    id_api: "'" + str(t['id']) + "'",
                    server_api: server.id,
                    'attribute_id': atributo.id
                }
                self.json_execute_create('product.attribute.value', data)

    @api.model
    def check_attributes(self, at, server):
        at_id = None
        existe = self.env['product.attribute'].search([(id_api, '=', str(at['id'])), (server_api, '=', int(server.id))])
        if not existe:
            # json = self.json_fields(attr, 'products/attributes', wcapi,server)
            # raise ValidationError(json['create']['server'])
            data = {
                'name': "'" + str(at['name']) + "'",
                id_api: "'" + str(at['id']) + "'",
                server_api: server.id,
                'create_variant': "'no_variant'",
                'display_type': "'radio'",
                'conector': f"'{server.conector}'"
            }
            self.json_execute_create('product.attribute', data)
        # insertar sus terminod

        # raise
        existe = self.env['product.attribute'].search([(id_api, '=', str(at['id'])), (server_api, '=', int(server.id))])
        self.inser_terminos(at['values'], existe, server)
        return existe
