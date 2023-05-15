odoo.define('whatsapp_connector_show_all_conversation.init_conversation', function(require) {
"use strict";

var InitConversation = require('whatsapp_connector.chat_classes').InitConversation;
var session = require('web.session');

InitConversation.include({
    
    /**
     * Domain para searchDefaultConversations
     * @returns {List<Object>} Lista con las condiciones
     */
    getDefaultSearchConversationsDomain: function() {
        let out;
        if (this.parent.chat_tab_filter == 'mines') {
            out = [['agent_id', '=', session.uid]]
        } else {
            out = [];
        }
        return out;
    },

    /**
     * Retorna el orden para searchDefaultConversations
     * @returns {List<String>} Orden
     */
    getDefaultSearchConversationsOrder: function() {
        return [];
    },

    /**
     * Busca los conversaciones
     * @returns {Promise}
     */
    searchDefaultConversations: function(){
        let model = 'acrux.chat.conversation';
        let domain = this.getDefaultSearchConversationsDomain();
        let order = this.getDefaultSearchConversationsOrder();
        return this._rpc({
            model: model,
            method: 'search_read',
            args: [domain, this.parent.conversation_used_fields, 0, 20, order],
            context: this.context 
        }).then(result => {
            result = this.postProcessorResult(result);
            this.conv_list = result;
        });
    },
    
    /**
     * @override
     * @see InitConversation.selectConversation
     * @returns {Promise}
     */
    selectConversation: function(event) {
        this.from_show_all_conversation = true;
        return this._super(event).then(() => this.from_show_all_conversation = false);
    },

    /**
     * @override
     * @see InitConversation.initAndNotify
     * @returns {Promise}
     */
    initAndNotify: function(conversation_id) {
        let out = false;
        if (this.from_show_all_conversation) {
            out = this._rpc({
                model: this.parent.model,
                method: 'build_dict',
                args: [[conversation_id], 22],
                context: this.context
            }).then(result => this.parent.onInitConversation(result[0]))
        } else {
            out = this._super(conversation_id);
        }
        return out;
    },
});

});
