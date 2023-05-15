
from odoo import models


class Conversation(models.Model):

    _inherit = 'acrux.chat.conversation'

    def write(self, vals):
        def build_dict(record):
            out = {'status': record.status}
            if record.agent_id:
                out['agent_id'] = [record.agent_id.id, record.agent_id.name]
            else:
                out['agent_id'] = [False, '']
            return out

        old_data = {}
        if self.env.context.get('chatroom_tab_admin'):
            for record in self:
                old_data[record.id] = build_dict(record)
        out = super(Conversation, self).write(vals)
        if self.env.context.get('chatroom_tab_admin'):
            notify = []
            for record in self:
                notify.append({
                    'from': old_data[record.id],
                    'conversation': record.build_dict(22)[0]
                })
            channel = self.get_channel_to_many()
            self._sendone(channel, 'changes_from_admin', notify)
        return out

    def block_conversation(self):
        out = super(Conversation, self).block_conversation()
        self.notify_admin()
        return out

    def release_conversation(self):
        super(Conversation, self).release_conversation()
        self.notify_admin()

    def send_message_bus_release(self, msg_data, back_status, check_access=True):
        super(Conversation, self).send_message_bus_release(msg_data, back_status, check_access=check_access)
        self.notify_admin()

    def notify_admin(self):
        admin_group_id = self.sudo().env.ref('whatsapp_connector_admin.group_chat_admin')
        notifications = []
        for user in admin_group_id.users:
            notifications.append((self.get_channel_to_one(user), 'admin_update', True))
        if notifications:
            self._sendmany(notifications)
