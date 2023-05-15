odoo.define('whatsapp_connector_admin.chat_classes', function(require) {
"use strict";

var chat = require('whatsapp_connector.chat_classes');

return _.extend(chat, {
    ConversationTree: require('whatsapp_connector_admin.conversation_tree'),
});
});