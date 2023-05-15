odoo.define('whatsapp_connector_admin.conversation_tree', function(require) {
"use strict";

var TreeView = require('whatsapp_connector.tree_view');

/**
 * Widget que maneja el tree de conversations
 *
 * @class
 * @name ConversationTree
 * @extends web.Widget.TreeView
 * @see acrux_chat.form_view
 */
var ConversationTree = TreeView.extend({
    /**
     * @override
     * @see Widget.init
     */
    init: function(parent, options) {
        if (options) {
            options.model = 'acrux.chat.conversation';
        }
        this._super.apply(this, arguments);

        this.parent = parent;
        this.context = _.extend({ search_default_filter_status_new: true,
                                  search_default_filter_status_current: true,
                                  chatroom_tab_admin: true,
                                  please_log_event: true},
                                this.context);
    },

    /**
     * @override
     * @see TreeView.start
     */
    start: function() {
        return this._super().then(() => this.parent.product_search.minimize());
    },

});

return ConversationTree;
});
