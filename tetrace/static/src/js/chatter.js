odoo.define('tetrace.Chatter', function (require) {
"use strict";

var Chatter = require('mail.Chatter');
var mailUtils = require('mail.utils');
var core = require('web.core');

var _t = core._t;
var QWeb = core.qweb;
    
Chatter.include({
    _onOpenComposerMessage: function () {
        var self = this;
        if (!this._suggestedPartnersProm) {
            this._suggestedPartnersProm = new Promise(function (resolve, reject) {
                self._rpc({
                    route: '/mail/get_suggested_recipients',
                    params: {
                        model: self.record.model,
                        res_ids: [self.context.default_res_id],
                    },
                }).then(function (result) {
                    if (!self._suggestedPartnersProm) {
                        return; // widget has been reset (e.g. we just switched to another record)
                    }
                    var suggested_partners = [];
                    var thread_recipients = result[self.context.default_res_id];
                    _.each(thread_recipients, function (recipient) {
                        var parsed_email = recipient[1] && mailUtils.parseEmail(recipient[1]);
                        suggested_partners.push({
                            checked: false,
                            partner_id: recipient[0],
                            full_name: recipient[1],
                            name: parsed_email[0],
                            email_address: parsed_email[1],
                            reason: recipient[2],
                        });
                    });
                    resolve(suggested_partners);
                });
            });
        }
        this._suggestedPartnersProm.then(function (suggested_partners) {
            self._openComposer({ isLog: false, suggested_partners: suggested_partners });
        });
    },
})
    
return Chatter;

});