odoo.define('mail.form_renderer', function (require) {
"use strict";

var Chatter = require('mail.Chatter');
var FormRenderer = require('web.FormRenderer');

FormRenderer.include({
    _renderNode: function (node) {
        var self = this;
        if (node.tag === 'div' && node.attrs.class === 'oe_chatter') {
            if (!this.chatter) {
                if(this.state != undefined && this.state.model == "hr.employee"){
                    options = {
                        isEditable: this.activeActions.edit,
                        viewType: 'form',
                        disable_attachment_box: 'disable_attachment_box'
                    };
                }else{
                    options = {
                        isEditable: this.activeActions.edit,
                        viewType: 'form',
                    };
                }
                this.chatter = new Chatter(this, this.state, this.mailFields, options);

                var $temporaryParentDiv = $('<div>');
                this.defs.push(this.chatter.appendTo($temporaryParentDiv).then(function () {
                    self.chatter.$el.unwrap();
                    self._handleAttributes(self.chatter.$el, node);
                }));
                return $temporaryParentDiv;
            } else {
                this.chatter.update(this.state);
                return this.chatter.$el;
            }
        } else {
            return this._super.apply(this, arguments);
        }
    },
});

});
