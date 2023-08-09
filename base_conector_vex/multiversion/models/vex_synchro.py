from odoo import api, fields, models
import threading
import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

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
    _inherit = "vex.synchro"