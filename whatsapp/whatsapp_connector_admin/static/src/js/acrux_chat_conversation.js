odoo.define('whatsapp_connector_admin.conversation', function(require) {
"use strict";

var Conversation = require('whatsapp_connector.conversation');

/**
 *
 * @class
 * @name Conversation
 * @extends whatsapp.Conversation
 */
Conversation.include({

    /**
     * @override
     * @see Conversation.update
     */
    update: function(options) {
        this._super.apply(this, arguments);
        this.admin_moved = options.admin_moved || false;
    },
 
    /**
     * @override
     * @see Conversation.showMessages
     */
    showMessages: function() {
        this.admin_moved = false;
        this.$('.o_acrux_admin_moved').remove();
        return this._super.apply(this, arguments);
    },
 
});

return Conversation;
});
