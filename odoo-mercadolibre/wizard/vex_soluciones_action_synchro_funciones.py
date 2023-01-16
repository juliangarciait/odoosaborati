from odoo import api, fields, models
import requests
from ..models.vex_soluciones_meli_config  import API_URL, INFO_URL, get_token , CATEGORIES_REQUIRED_ATRR , CATEGORIES_REQUIRED_BRAND
import logging
_logger = logging.getLogger(__name__)
import pprint
import base64
from odoo.addons.payment.models.payment_acquirer import ValidationError

id_api       = 'id_vex'
server_api   = 'server_vex'
class MeliActionSynchro(models.TransientModel):
    _inherit       = "vex.synchro"
    server_meli    = fields.Many2one('meli.synchro.instance',"Instance")

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
                    #exist = self.env['meli.synchro.instance'].search([('user_id', '=', str(server.user_id))])
                    server.write(update)
        return res

    def start_import(self):
        res = super(MeliActionSynchro, self).start_import()
        if self.conector == 'meli':
            id_action = 'odoo-mercadolibre.action_view_meli_synchro'
            return self.vex_import(id_action,None)
        return res

    @api.model
    def insert_variations(self, dr, server, creado, accion, queryx = '' ):
        # recorrer las variantes y chekar todas los atrbutos
        # guardar el id por atributo y luego colocarlo en el respect
        variantes_array = {'ja'}
        values_array = {'ja'}
        #obtener las variantes
        variants = dr['variations']
        #raise ValidationError(str(len(variants)))

        if variants:
            #bucle a las variantes
            master_data_values_ids = []
            ct = 0
            insert_vari = ''
            for index, v in enumerate(variants):
                ct += 1
                data_values_ids = []
                for vi in v['attribute_combinations']:
                    # verificar el atributo
                    at = self.check_attributes(vi, server)
                    # raise ValidationError(at)
                    variantes_array.add(at.id)
                    json_at = []
                    if at:
                        '''
                        data = {
                            'active': True,
                            'attribute_id': int(at.id),
                            'product_tmpl_id': int(creado.id),

                        }
                        '''
                        #self.env['vex.web.services'].create_update()

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
                            for vx in vi['values']:
                                # raise ValidationError(vx)
                                vv = None

                                if not vx['name'] in va_array:
                                    vv = self.check_terminos(vx['name'], server, at,creado)

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
                                         ('product_tmpl_id', '=', creado.id),
                                         ('attribute_line_id', '=', atl.id)])
                                    data_values_ids.append(line_v.id)

                                values_array.add(str(at.id) + '_' + vx['name'])

                        else:
                            raise ValidationError('errorr')
                    else:
                        raise ValidationError('o noo')

                domain_varition = [('product_tmpl_id', '=', int(creado.id)), ('id_vex_varition', '=', False)]
                #'|', ('active', '=', True), ('active', '=', False)

                #raise ValidationError(str([v,dr]))


                pppi = self.env['product.product'].search(domain_varition)

                if pppi:
                    write = {
                        ' active ': "'t'",
                        'id_vex_varition': "'"+str(v['id'])+"'",
                        'stock_vex': v['available_quantity'],
                        'vex_regular_price': v['price'],
                        'base_unit_count': 0
                    }
                   

                    self.json_execute_update('product.product', write, pppi.id)


                master_data_values_ids.append(data_values_ids)
                ppp = self.env['product.product'].search(
                    [('product_tmpl_id', '=', int(creado.id)), ('id_vex_varition', '=', str(v['id'])),
                     '|', ('active', '=', True), ('active', '=', False)])
                if not ppp:
                    #raise ValidationError('porque')
                    create = {
                        'active': "'t'",
                        'product_tmpl_id': creado.id,
                        'id_vex_varition': "'" + str(v['id']) + "'",
                        'vex_regular_price': v['price'],
                        'stock_vex': v['available_quantity'],
                        'base_unit_count': 0
                    }
                    insert_vari += self.json_execute_create('product.product', create,True)

                else:
                    write = {
                        ' active ': "'t'",
                        'vex_regular_price': v['price'],
                        'stock_vex': v['available_quantity'],
                        'base_unit_count': 0
                    }
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
            #crear product de template
            ppp = self.env['product.product'].search([('product_tmpl_id', '=', int(creado.id)),
                                                      ('id_vex_varition', '=', str(creado.id_vex)),
                                                      '|', ('active', '=', True), ('active', '=', False)])
            if not ppp:
            # 1==1:
                create = {
                    ' active ': "'t'",
                    'product_tmpl_id': creado.id,
                    'id_vex_varition': "'" + str(creado.id_vex) + "'",
                    'stock_vex': dr['available_quantity'],
                    'base_unit_count': 0
                    #'vex_regular_price': v['price']
                }
                #raise ValidationError(str(dr))
                self.json_execute_create('product.product', create)

        self.invalidate_cache()
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

