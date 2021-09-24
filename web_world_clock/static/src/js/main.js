odoo.define('web_world_clock.hora_dashboard', function(require){
"use strict";

var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');
var AbstractWebClient = require('web.AbstractWebClient');
var HomeMenu = require('web_enterprise.HomeMenu');

var _t = core._t;
var QWeb = core.qweb;


HomeMenu.include({

    init: function (parent, menuData) {
        this._super.apply(this, arguments);
    },

    start: function () {
        var self = this;
        this.$horasDashboard = this.$('.o_horas_dashboard');
        return this._super.apply(this, arguments);
    },

    _render: function () {
        this.$horasDashboard.html(QWeb.render('web_world_clock.Content', { horas: this.horas }));
        return this._super();
    },
});

});
