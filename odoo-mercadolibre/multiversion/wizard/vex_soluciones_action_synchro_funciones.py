from odoo import api, fields, models
import requests
from ..models.vex_soluciones_meli_config  import API_URL, INFO_URL, get_token , CATEGORIES_REQUIRED_ATRR , CATEGORIES_REQUIRED_BRAND
import logging
_logger = logging.getLogger(__name__)
import pprint
import base64
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

id_api       = 'id_vex'
server_api   = 'server_vex'
class MeliActionSynchro(models.TransientModel):
    _inherit       = "vex.synchro"

    
    
    def insert_meli_payment(self, lines, server, creado, accion):
        for line in lines:
            if line['operation_type'] == 'payment_addition' and line['status'] == 'approved':
                existe = server.product_payment_add
                if not existe:
                    raise ValidationError('NO DEFINIO UN PRODUCTO PARA DINERO AGREGADO')
                tax_product = server.tax_id
                if server.use_tax_product:
                    tax_product = existe.taxes_id
                    if tax_product:
                        if len(tax_product) > 1:
                            raise ValidationError('EL PRODUCTO TIENE MAS DE UN IMPUESTO')

                price_unit = float(line['total_paid_amount'])

                if tax_product:
                    if tax_product.amount != 0:
                        with_tax = float(line['total_paid_amount'])
                        without_tax = (100 * with_tax) / (100 + tax_product.amount)
                        price_unit = without_tax

                    # raise ValidationError(str([p['unit_price'],tax_amount,price_unit,creado.id_vex]))

                new_line = {
                    # 'name':str(existe.name),
                    'name': "'" + str(line['reason']) + "'",
                    'product_id': existe.id,
                    'product_uom_qty': 1,
                    'price_unit': price_unit,
                    # 'price_reduce': float(p['unit_price']),
                    # 'price_reduce_taxinc': float(p['unit_price']),
                    # 'price_reduce_taxexcl': float(p['unit_price']),
                    'order_id': creado.id,
                    # 'price_subtotal': float(p['unit_price']) * int(p['quantity']),
                    # 'price_total': float(p['unit_price']) * int(p['quantity']),
                    # 'price_tax': 0.0,
                    # campos requeridos
                    'customer_lead': 1.0,
                    # 'invoice_status': "'no'",
                    'company_id': server.company.id,
                    'currency_id': server.pricelist.currency_id.id,
                    'product_uom': 1,
                    # 'discount': 0

                }
                if tax_product:
                    new_line['tax_id'] = [(6, 0, [tax_product.id])]

                self.env['sale.order.line'].create(new_line)

        return 

    @api.model
    def check_terminos(self, t, server, atr,creado=None):

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
                    'name': "'"+str(t['name'])+"'",
                    id_api: "'"+str(t['id'])+"'",
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
                'name': "'"+str(at['name'])+"'",
                id_api: "'"+str(at['id'])+"'",
                server_api: server.id,
                'create_variant': "'no_variant'",
                'display_type': "'radio'",
                'conector': "'meli'"
            }
            self.json_execute_create('product.attribute',data)
        # insertar sus terminod

        # raise
        existe = self.env['product.attribute'].search([(id_api, '=', str(at['id'])), (server_api, '=', int(server.id))])
        self.inser_terminos(at['values'], existe , server)
        return existe

    def check_synchronize(self,server):
        res = super(MeliActionSynchro, self).check_synchronize(server)
        if server.conector == 'meli':
            access_token = server.access_token
            res = requests.get(INFO_URL, params={'access_token': access_token})

            if res.status_code != 200:
                token = get_token(server.app_id, server.secret_key, server.redirect_uri, '', server.refresh_token)
                if token:
                    update = {
                        'access_token' : token['access_token'],
                        'refresh_token' : token['refresh_token'],
                    }

                    server.write(update)
        return res



    def start_import(self):
        res = super(MeliActionSynchro, self).start_import()
        if self.conector == 'meli' :
            server = self.server_vex
            id_action = 'odoo-mercadolibre.action_view_meli_synchro'
            res = self.vex_import(id_action,None)
            if self.accion.argument == 'products':
                lines_wait = self.env['vexlines.import'].search([('accion', '=', self.accion.id),
                                                                 ('instance', '=', server.id),
                                                                 ('instance', '=', server.id), ('state', '=', 'wait')],
                                                                limit=1)
                if lines_wait:
                    for line in lines_wait:
                        res = self.start_import()

            if self.accion.argument == 'orders':
                self.meli_validate_status_pending_orders()
                for i in range(5):
                    self.meli_validate_status_pending_orders()

            
            return res
        return res


    @api.model
    def insert_variations(self, dr, server, creado, accion, sku,queryx = '' ):
        #creado.id_vex = dr['id']
        #raise ValidationError(str([sku,creado,dr]))


        # recorrer las variantes y chekar todas los atrbutos
        # guardar el id por atributo y luego colocarlo en el respect
        variantes_array = {'ja'}
        values_array = {'ja'}
        #obtener las variantes

        variants = dr['variantes']
        #raise ValidationError(str(len(variants)))

        if variants:
            #bucle a las variantes
            master_data_values_ids = []

            insert_vari = ''
            #raise ValidationError(str(variants))
            for index, v in enumerate(variants):
                creadox = creado
                '''
                
                if len(creadox) > 1 :
                    #creadox = self.env['product.product'].search([('id_vex_varition', '=', v['id'])]).product_tmpl_id
                    exist_conector = self.env['vex.product.product.conector'].search([
                        ('id_vex_varition', '=', v['id']), ('instance', '=', server.id)
                    ])
                    if exist_conector:
                        creadox = exist_conector.product_id
                    #('product_id', '=', exist.id),
                    #if not exist_conector:
                    #    exist_conector = self.env['vex.product.product.conector'].create({
                    #        'product_id': exist.id,
                    #        'id_vex_varition': id_vex,
                    #        'id_vex': id_vex,
                    #        'instance': server.id
                    #    })
                #if not creadox:
                #    creadox = self.env['product.template'].search([('id_vex', '=', dr['id']),('create_of_meli','=',True)])
                '''
                exist_vari = False
                sku_vari = None

                for atributes in v['attributes']:
                    if atributes['id'] == 'SELLER_SKU':
                        sku_vari = atributes['value_name']
                        default_code = atributes['value_name']
                        exist_product = self.env['product.product'].search([('default_code', '=', default_code)])

                        if exist_product and len(exist_product) > 1:
                            raise ValidationError(
                                f'''El Producto con sku {default_code} tiene mas de un registro''')

                        if exist_product:
                            exist_vari = True
                            continue
                        if  exist_product:

                            exist_conector = self.env['vex.product.product.conector'].search([
                                ('product_id', '=', exist_product.id), ('id_vex_varition', '=', v['id']),
                                ('instance', '=', server.id)
                            ])
                            if not exist_conector:
                                exist_conector = self.env['vex.product.product.conector'].create({
                                    'product_id': exist_product.id,
                                    'id_vex_varition':v['id'],
                                    'id_vex': dr['id'],
                                    'instance': server.id
                                })

                            try:
                                exist_product.meli_logistic_type = dr['shipping']['logistic_type']
                            except:
                                exist_product.meli_logistic_type = False

                            exist_vari = True



                #raise ValueError(creado)
                if exist_vari:
                    continue

                if not server.create_not_exists:
                    continue


                data_values_ids = []
                for vi in v['attribute_combinations']:
                    # verificar el atributo
                    at = self.check_attributes(vi, server)
                    # raise ValidationError(at)
                    variantes_array.add(at.id)
                    json_at = []
                    if at:
                        # buscar si existe el atributo en atribute line
                        atl = self.env['product.template.attribute.line'].search(
                            [('attribute_id', '=', int(at.id)), ('product_tmpl_id', '=', int(creadox.id))])

                        if not atl:
                            data = {
                                ' active ': "'t'",
                                'attribute_id': int(at.id),
                                'product_tmpl_id': int(creadox.id),

                            }
                            if len(creado) > 1 or creado == 0 or creado.id == 0 or not creado:
                                raise ValueError([creado, at.display_name, v, data, dr])

                            self.json_execute_create('product.template.attribute.line', data)



                            # currents = self._cr.dictfetchall()
                            # raise ValidationError(currents)
                            atl = self.env['product.template.attribute.line'].search(
                                [('product_tmpl_id', '=', creadox.id), ('attribute_id', '=', at.id)])

                        if atl:
                            # verificar si existe ese valor  en ese atributo line
                            valores_actuales = atl.value_ids
                            # raise ValidationError(valores_actuales)
                            va_array = []
                            for va in valores_actuales:
                                va_array.append(va.name)
                            # raise ValidationError(va_array)
                            for vx in vi['values']:
                                # raise ValidationError(vx)
                                vv = None

                                if not vx['name'] in va_array:
                                    vv = self.check_terminos(vx['name'], server, at,creadox)

                                    #raise ValidationError('aabt' + str(pppi))
                                    # raise ValidationError('que')
                                    if vv:
                                        atl.value_ids += vv

                                else:
                                    vv = self.check_terminos(vx['name'], server, at)
                                    # raise ValidationError(vv)

                                if vv:
                                    line_v = self.env['product.template.attribute.value'].search(
                                        [('product_attribute_value_id', '=', vv.id), ('attribute_id', '=', at.id),
                                         ('product_tmpl_id', '=', creadox.id),
                                         ('attribute_line_id', '=', atl.id)])
                                    data_values_ids.append(line_v.id)

                                values_array.add(str(at.id) + '_' + vx['name'])

                        else:
                            raise ValidationError('errorr')
                    else:
                        raise ValidationError('o noo')
                exist_conector = self.env['vex.product.product.conector'].search([('id_vex_varition', '=', v['id']), ('instance', '=', server.id)])


                ppp = exist_conector.product_id

                if not ppp:
                    #raise ValueError([creado,creado.product_variant_ids])
                    #domain_varition = [('product_tmpl_id', '=', int(creadox.id))]
                    #if server.search_archive_products:
                    #    domain_varition.append('|')
                    #    domain_varition.append(('active', '=', True))
                    #    domain_varition.append(('active', '=', False))
                    #domainx = domain_varition
                    #ppp = self.env['product.product'].search(domain_varition)
                    for ph in creado.product_variant_ids:
                        if not ph.vex_conector_ids:
                            ppp = ph
                    #raise ValueError([ppp,ppp.vex_conector_ids])

                if ppp:
                    if len(ppp) > 1 :
                        raise ValueError([domainx,v['id'],sku_vari,dr])
                    write = {
                        ' active ': "'t'",
                    }
                    if sku_vari and not  ppp.default_code:
                        write['default_code'] = f"'{sku_vari}'"

                    try:
                        write['meli_logistic_type'] = f"'{dr['shipping']['logistic_type']}'"
                    except:
                        write['meli_logistic_type'] = " NULL "

                    

                    self.json_execute_update('product.product', write, ppp.id)

                    exist_conector = self.env['vex.product.product.conector'].search([
                        ('product_id', '=', ppp.id), ('id_vex_varition', '=', str(v['id'])), ('instance', '=', server.id)
                    ])
                    if not exist_conector:
                        try:
                            self.env['vex.product.product.conector'].create({
                                'product_id': ppp.id,
                                'id_vex_varition': str(v['id']),
                                'id_vex': dr['id'],
                                'instance': server.id
                            })
                        except:
                            pass




                master_data_values_ids.append(data_values_ids)
                #ppp = self.env['product.product'].search( [('id_vex_varition', '=', str(v['id'])),'|', ('active', '=', True), ('active', '=', False)])
                if not ppp:
                    raise ValueError([ppp,creadox,creadox.product_variant_ids,domainx])
                    create = {
                        'active': "'t'",
                        'product_tmpl_id': creadox.id,
                        #'id_vex_varition': "'" + str(v['id']) + "'",
                        #'vex_regular_price': v['price'],
                        #'stock_vex': v['available_quantity'],
                        'base_unit_count': 0 ,

                    }
                    if sku_vari:
                        create['default_code'] = f"'{sku_vari}'"
                        
                    try:
                        create['meli_logistic_type'] = f"'{dr['shipping']['logistic_type']}'"
                    except:
                        create['meli_logistic_type'] = " NULL "
                    insert_vari += self.json_execute_create('product.product', create,True)

                else:
                    write = {
                        ' active ': "'t'",
                        #'vex_regular_price': v['price'],
                        #'stock_vex': v['available_quantity'],
                        'base_unit_count': 0
                    }
                    #if sku_vari:
                    #    write['default_code'] = f"'{sku_vari}'"
                        
                    try:
                        write['meli_logistic_type'] = f"'{dr['shipping']['logistic_type']}'"
                    except:
                        write['meli_logistic_type'] = " NULL "
                    insert_vari +=  self.json_execute_update('product.product', write, ppp.id,True)



                for g in data_values_ids:
                    query_combi = "INSERT INTO product_variant_combination " \
                                  "(product_product_id,product_template_attribute_value_id) VALUES" \
                                  "({},{}) ON CONFLICT DO NOTHING".format(ppp.id, g)
                    insert_vari += "INSERT INTO product_variant_combination " \
                                  "(product_product_id,product_template_attribute_value_id) " \
                                  "( SELECT id as product_product_id ,  {} as product_template_attribute_value_id" \
                                  " FROM product_product WHERE id_vex_varition =  '{}') ON CONFLICT DO NOTHING ; \n".format( g , str(v['id']))
                    # raise ValidationError(query_combi)

                    #self.env.cr.execute(query_combi)

            #queryx += insert_vari
            #raise ValidationError(insert_vari)
            if insert_vari and insert_vari != '':
                self.env.cr.execute(insert_vari)



            if accion.import_images:
                for index, v in enumerate(variants):
                    ppp = self.env['product.product'].search([('product_tmpl_id', '=', int(creado.id)),

                                                              ('id_vex_varition', '=', str(v['id'])),
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
                    #raise ValidationError(ppp)

                    ppp.write({'image_1920': base64.b64encode(myimage.content)})


            #raise ValidationError(str(insert_vari))

        else:
            #raise ValidationError(sku)
            if sku:
                #raise ValueError([exist.id_vex, exist.product_variant_ids])
                if len(creado.product_variant_ids) == 1:
                    ppp = self.env['product.product'].search([('default_code', '=', sku)])
                    #ppp.id_vex_varition = dr['id']

                    #ppp.stock_vex = dr['available_quantity']
                    exist_conector = self.env['vex.product.product.conector'].search([
                        ('product_id', '=', ppp.id), ('id_vex_varition', '=', dr['id']), ('instance', '=', server.id)
                    ])
                    if not exist_conector:
                        exist_conector = self.env['vex.product.product.conector'].create({
                            'product_id': ppp.id,
                            'id_vex_varition': dr['id'],
                            'id_vex': dr['body']['id'],
                            'instance': server.id
                        })
                    try:
                        ppp.meli_logistic_type = dr['shipping']['logistic_type']
                    except:
                        ppp.meli_logistic_type = False

                    # raise ValidationError(ppp)
                else:
                    if  not server.create_not_exists:
                        return queryx


                    #raise ValueError([creado, creado.product_variant_ids ,  sku,dr])

                    # crear product de template
                    #ppp = self.env['product.product'].search([('product_tmpl_id', '=', int(creado.id)),
                    #                                          ('id_vex_varition', '=', str(creado.id_vex)),
                    #                                          '|', ('active', '=', True), ('active', '=', False)])
                    if creado and len(creado.product_variant_ids) == 0:

                        create = {
                            ' active ': "'t'",
                            'product_tmpl_id': creado.id,
                            #'id_vex_varition': "'" + str(dr['id']) + "'",
                            #'stock_vex': dr['available_quantity'],
                            'base_unit_count': 0,
                            'default_code': f"'{sku}'"
                            # 'vex_regular_price': v['price']
                        }
                        try:
                            create['meli_logistic_type'] = f"'{dr['shipping']['logistic_type']}'"
                        except:
                            create['meli_logistic_type'] = f" NULL "
                        # raise ValidationError(str(dr))
                        self.json_execute_create('product.product', create)
                        ppp = self.env['product.product'].search([('product_tmpl_id', '=', int(creado.id)),'|', ('active', '=', True), ('active', '=', False)])
                        if not ppp:
                            raise ValueError([dr, creado])
                        #raise ValueError([ppp,creado.product_variant_ids])
                        
                    else:
                        raise ValueError([dr, creado])

                
            else:
                if not server.create_not_exists:
                    return queryx

                raise ValueError([sku,dr,creado])
                if len(creado.product_variant_ids) == 1:
                    ppp = creado.product_variant_ids[0]
                    ppp.stock_vex = dr['available_quantity']
                    try:
                        ppp.meli_logistic_type = dr['shipping']['logistic_type']
                    except:
                        ppp.meli_logistic_type = False
                else:
                    # crear product de template
                    ppp = self.env['product.product'].search([('product_tmpl_id', '=', int(creado.id)),
                                                              ('id_vex_varition', '=', str(creado.id_vex)),
                                                              '|', ('active', '=', True), ('active', '=', False)])
                    if not ppp and server.create_not_exists:
                        # 1==1:

                        if not creado:
                            raise ValueError([dr,creado])
                        create = {
                            ' active ': "'t'",
                            'product_tmpl_id': creado.id,
                            'id_vex_varition': "'" + str(dr['id']) + "'",
                            'stock_vex': dr['available_quantity'],
                            'base_unit_count': 0
                            # 'vex_regular_price': v['price']
                        }
                        try:
                            create['meli_logistic_type'] = f"'{dr['shipping']['logistic_type']}'"
                        except:
                            create['meli_logistic_type'] = " NULL "

                        # raise ValidationError(str(dr))
                        self.json_execute_create('product.product', create)




        #raise ValidationError('OKKK')

        #self.invalidate_cache()
        return queryx

    @api.model
    def check_imagenes(self, imagenes, server, exist):
        # verificar las imagenes
        img_str = ''

        #imagenes_array = {'ja'}

        for i in imagenes:
            img_str += self.check_picture(i, server, exist)
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


    @api.model
    def check_picture(self, image, server, product):

        img_str = ''
        # verificar si la imagen existe
        img = product.product_template_image_ids.search([(id_api, '=', image['id']),
                                                         (server_api, '=', server.id)
                                                         ], limit=1)
        if not img:
            url = image['url']

            '''
                        try:
                myfile = requests.get(url)
            except requests.ConnectionError:
                return
            data = {
                id_api: image['id'],
                server_api: server.id,
                'conector': server.conector,
                'image_1920': base64.b64encode(myfile.content),
                'product_tmpl_id': product.id,
                'name': image['id'],

            }
            img = self.env['product.image'].create(data)
            
            '''

            #raise ValidationError(url)

            data = {
                id_api: "'{}'".format(image['id']),
                server_api: server.id,
                'conector': "'{}'".format(server.conector),
                'image_url_vex': "'{}'".format(url),
                'product_tmpl_id': product.id,
                'name':  "'{}'".format(image['id']),

            }


            img_str = self.json_execute_create('product.image',data,True)
        else:
            url = image['url']
            '''
            try:
                myfile = requests.get(url)
                myfile = base64.b64encode(myfile.content)
            except requests.ConnectionError:
                return
            '''
            if img.image_url_vex != url:
                data = {
                    'dowloaded': "'f'",
                }

                img_str = self.json_execute_update('product.image', data, img.id, True)



            #img.write()

            #raise ValidationError(product)
        return img_str

    def insert_categorias_children_meli(self,id_vex,server,exist):
        #raise ValidationError('oki')
        dr = self.get_category(id_vex)
        #raise ValidationError(str(dr))
        if 'path_from_root' in dr:
            if dr['path_from_root']:
                datavs = []
                parent_id = None
                for d in dr['path_from_root']:
                    # raise ValidationError(pt)
                    dg = {
                        'name': d['name'],
                        'id_vex': d['id'],
                        'conector': 'meli',
                        # 'parent_id': exist.id,

                    }
                    if parent_id:
                        dg['parent_id_vex_tmp'] = d['id']


                    if d['id'] in CATEGORIES_REQUIRED_ATRR:
                        dg['required_manufacture_meli'] = True
                    if d['id'] in CATEGORIES_REQUIRED_BRAND:
                        dg['required_brand_meli'] =  True
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
                for d in dr['children_categories']:
                    # raise ValidationError(pt)
                    if not exist.id:
                        raise ValidationError(d['name'])
                    dg = {
                        'name': d['name'],
                        'id_vex': d['id'],
                        'conector': 'meli',
                        'parent_id': exist.id,
                        # 'parent_path': pt
                    }

                    if d['id'] in CATEGORIES_REQUIRED_ATRR:
                        dg['required_manufacture_meli'] =  True
                    if d['id'] in CATEGORIES_REQUIRED_BRAND:
                        dg['required_brand_meli'] =  True
                    datav.append(dg)
                datar = {
                    'model': 'product.public.category',
                    'data': datav,
                    'identiquer_keys': ['id_vex', 'conector']

                }
                self.env['vex.web.services'].create_update(datar)

    def execute_before_create(self,data, query, server, table, accion, id_vex,queryx ):
        create_tmp = super().execute_before_create(data, query, server, table, accion, id_vex,  queryx)
        if  query == "products" and server.conector == 'meli':
            body = data['body']
            #raise ValidationError(str(body))

            if 'variantes' in body:
                if body['variations']:
                    exist_all_variants = True
                    for variant in body['variantes']:
                        if 'attributes' in body:
                            have_sku = False
                            for atributes in variant['attributes']:
                                if atributes['id'] == 'SELLER_SKU':
                                    have_sku = True
                                    default_code = atributes['value_name']
                                    exist_product = self.env['product.product'].search([('default_code','=',default_code)])
                                    if exist_product and len(exist_product) > 1 :
                                        raise ValidationError(f'''El Producto con sku {default_code} tiene mas de un registro''')
                                    if not exist_product:
                                        exist_all_variants = False
                                    #else:
                                    #    raise ValidationError(default_code)
                            if not have_sku:
                                exist_product = self.env['product.product'].search([('id_vex_varition', '=', variant['id'])])
                                if exist_product and len(exist_product) > 1:
                                    raise ValidationError(
                                        f'''El Producto con ID Varition {variant['id']} tiene mas de un registro''')
                                if not exist_product:
                                    exist_all_variants = False





                    if exist_all_variants:
                        create_tmp = False

        #raise ValidationError(create_tmp)


        return create_tmp
 
 
    def aditional_validatione_exist(self, id_vex, query, table ,  server, data):
        #raise ValueError(exist)

        res = super().aditional_validatione_exist(id_vex, query, table ,  server, data)
        if server.conector == 'meli' and query == 'orders':

            domain = [(server.id_external_aditional_order.name, 'ilike', str(data['id']))]
            exist = self.env['sale.order'].search(domain)
            
            if not exist:
                domain = [('meli_shop_id', '=', str(data['id']))]
                existl = self.env['sale.order.line'].search(domain)
                if existl:
                    exist = existl.order_id

            #raise ValueError(exist, exist.id_vex,domain )
            #raise ValueError(exist)
            if exist:
                return exist

        #raise ValueError(res)

        return res
