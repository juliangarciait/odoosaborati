odoo.define('whatsapp_connector_admin.acrux_chat', function(require) {
"use strict";

var chat = require('whatsapp_connector.chat_classes');
var AcruxChatAction = require('whatsapp_connector.acrux_chat').AcruxChatAction
var framework = require('web.framework');
var session = require('web.session');
var core = require('web.core');
var _t = core._t;


/**
 * @class
 * @name AcruxChatAction
 * @extends AcruxChatAction
 */
AcruxChatAction.include({
    events: _.extend({}, AcruxChatAction.prototype.events, {
        'click li#tab_admin': 'tabAdmin',
    }),

    /**
     * Hace trabajos de render
     *
     * @private
     * @returns {Promise} Para indicar que termino
     */
    _initRender: function() {
        return this._super().then(() => {
            this.$tab_content_admin = this.$('div#tab_content_admin > div.o_group');
            return session.user_has_group('whatsapp_connector_admin.group_chat_admin').then(hasGroup => {
                if (!hasGroup) {
                    this.$('li#tab_admin').addClass('d-none');
                }
                this.is_user_admin = hasGroup;                
            })
        });
    },

    /**
     * @override
     * @see AcruxChatAction.getRequiredViews
     * @returns {Promise}
     */
    getRequiredViews: function() {
        return this._super().then(() => {
            return this._rpc({
                model: this.model,
                method: 'check_object_reference',
                args: ['_admin', 'view_whatsapp_connector_conversation_inline_chat_tree'],
                context: this.context
            }).then(result => {
                this.conversation_tree_view = result[1];
            });
        });
    },

    /**
     * @override
     * @see AcruxChatAction.notifactioProcessor
     */
    notifactionProcessor: function(data) {
        this._super(data);
        if (data.type === 'changes_from_admin') {
            framework.blockUI();
            data.payload.forEach(m => this.onChangeFromAdmin(m));
            if (this.user_status.isActive()) {
                this.showConversations();
            }
            if (this.$tab_init_chat.hasClass('active')) {
                this.init_conversation.renderConvList();
            } else if (this.$tab_content_admin.parent().hasClass('active')) {
                this.conversation_tree.acrux_form_widget.reload();
            }
            framework.unblockUI();
        }
        if ((data.type === 'admin_update' || data.type === 'update_conversation')
            && this.user_status.isActive()) {
            if (this.$tab_content_admin.parent().hasClass('active')) {
                this.conversation_tree.acrux_form_widget.reload();
            }
        }
    },

    /**
     * @override
     * @see AcruxChatAction.onNewMessage
     * @returns {Promise}
     */
    onNewMessage: function(d) {
        let conv = this.conversations.find(x => x.id == d.id);
        conv = Object.assign({}, conv);
        return this._super(d).then(result => {
            if (this.$tab_content_admin.parent().hasClass('active')) {
                if (!conv || (conv.status != d.status)) {
                    this.conversation_tree.acrux_form_widget.reload();
                }
            }
            return result;
        });
    },

    /**
     * Un administrador hizo un cambio a una conversación, se notificó a todos
     * los usuarios, y se verificará, el cambio de la conversación y el proces
     * a seguir.
     *
     * @param {Object} data cambio del admin
     * @returns {Promise}
     */
    onChangeFromAdmin: function(data) {
        let new_conv = data.conversation;
        let conv = this.conversations.find(x => x.id == new_conv.id);
        
        new_conv.admin_moved = true;
        if(conv) {
            conv.update(new_conv);
            this.conversations = this.conversations.filter(x => x.id != conv.id);
            if (this.is_user_admin) {
                this.conversations.unshift(conv);
            } else {
                if (conv.status === 'new' || conv.isMine()) {
                    this.conversations.unshift(conv);
                }
            }
            if (this.selected_conversation) {
                if (this.conversations.includes(this.selected_conversation)) {
                    this.selectConversation({ currentTarget: this.selected_conversation.el })
                } else {
                    this.removeSelectedConversation()
                }
            }
        } else {
            conv = new_conv = new chat.Conversation(this, new_conv)
            if (new_conv.status === 'new' || new_conv.isMine()) {
                this.conversations.unshift(new_conv);
            }
        }
        if (this.$tab_init_chat && this.$tab_init_chat.hasClass('active')) {
            this.init_conversation.update(new_conv);
        }
        return Promise.resolve(conv);
    },

    /**
     * Cuando se hace clic en el tab de CRM, se muestra un formulario
     * de crm.lead
     *
     * @param {Event} _event
     * @param {Object} data
     * @return {Promise}
     */
    tabAdmin: function(_event, data) {
        let out = Promise.reject()

        if (this.is_user_admin) { 
            this.saveDestroyWidget('conversation_tree')
            let options = {
                context: this.action.context,
                action_manager: this.action_manager,
                form_name: this.conversation_tree_view,
                title: _t('Admin'),
            }
            this.conversation_tree = new chat.ConversationTree(this, options);
            this.$tab_content_admin.empty()
            out = this.conversation_tree.appendTo(this.$tab_content_admin);
        } else {
            this.env.services.crash_manager.show_warning({message: _t('You do not have permission to see this tab.')})
        }
        out.then(() => data && data.resolve && data.resolve())
        out.catch(() => data && data.reject && data.reject())
        return out
    },

    /**
     * @override
     * @see AcruxChatAction.tabNeedReload
     */
    tabNeedReload: function() {
        return (this._super() && !this.$tab_content_admin.parent().hasClass('active'));
    },

    
    /**
     * @override
     * @see AcruxChatAction._getMaximizeTabs
     */
    _getMaximizeTabs: function() {
        let out = this._super();
        out.push("#tab_content_admin")
        return out;
    },
    
    /**
     * Devuelve si el controlador es parte de chatroom, es util para los tabs
     * @param {String} jsId id del controllador
     * @returns {Boolean}
     */
    isChatroomTab: function(jsId) {
        return this._super(jsId) || this._isChatroomTab('conversation_tree', jsId)
    },

    /**
     * Muestra todas las conversaciones en el chat
     * @returns {Promise}
     */
    showConversations: function() {
        return this._super().then(() => {
            const defs = [];
            this.getDoneConversation().forEach(x => defs.push(this.renderNewConversation(x)));
            this.getCurrentNotMineConversation().forEach(x => defs.push(this.renderNewConversation(x)));
            return Promise.all(defs);
        })
    },

    /**
     * Returna la lista de conversaciones terminadas
     *
     * @returns {Array<Conversation>}
     */
    getDoneConversation: function() {
        return this.conversations.filter(x => x.status == 'done');
    },
    
    /**
     * Returna la lista de conversaciones no mias
     *
     * @returns {Array<Conversation>}
     */
    getCurrentNotMineConversation: function() {
        return this.conversations.filter(x => x.status == 'current' && !x.isMine());
    },
})

})
