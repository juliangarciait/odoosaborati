odoo.define('whatsapp_connector_show_all_conversation.acrux_chat', function(require) {
"use strict";

var AcruxChatAction = require('whatsapp_connector.acrux_chat').AcruxChatAction;
var session = require('web.session');


AcruxChatAction.include({
    events: _.extend({}, AcruxChatAction.prototype.events, {
        'click li#tab_init_chat': 'tabInitChat',
    }),

    /**
     * @override
     * @see Widget.willStart
     */
    willStart: function() {
        return Promise.all([
            this._super(),
            this._rpc({
                model: 'res.users',
                method: 'read',
                args: [[session.uid], ['chat_tab_filter']],
                context: this.context
            }).then(result => {
                this.chat_tab_filter = result[0].chat_tab_filter;
            })
        ]);
    },

    /**
     * Muestra la pestaña con todos los chats
     *
     * @param {Event} _event
     * @param {Object} data
     * @return {Promise}
     */
    tabInitChat: function(_event, data) {
        let out = Promise.reject()

        this.init_conversation.empty();
        out = this.init_conversation.searchDefaultConversations().then(() => {
            this.init_conversation.renderConvList();
        })
        out.then(() => data && data.resolve && data.resolve())
        out.catch(() => data && data.reject && data.reject())
        return out
    }
});

});
