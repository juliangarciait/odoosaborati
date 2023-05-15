# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    chat_tab_filter = fields.Selection([('all', 'All'), ('mines', 'Mines')],
                                       string='Chat tab filter ', required=True,
                                       default='all')

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['chat_tab_filter']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['chat_tab_filter']
