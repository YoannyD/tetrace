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
//        this.horas = this._getHoras();
    },

//    _getHoras: function (){
//        var self = this;
//        this._rpc({
//            model: 'res.config.settings',
//            method: 'horas_dashboard',
//            domain: [],
//        })
//        .then(function(res) {
//            console.log("cosas devueltas");
//            console.log(res);
//            return res
////            self.$(".lst_horas").appendTo("<li>Alemani</li>");
////            res = res[0];
////            if (res.show_clock) {
////                setInterval(self.renderTime, 1000);
////            }
//        });
//    },

    start: function () {
        var self = this;
        this.$horasDashboard = this.$('.o_horas_dashboard');
        return this._super.apply(this, arguments);
    },

    _render: function () {
        this.$horasDashboard.html(QWeb.render('web_world_clock.Content', { horas: this.horas }));
        return this._super();
    },
//    renderTime: function(){
//        this.$(".main_clock").text(clockTemp.getTime());
//    },
//    getTime: function() {
//    	  var today = new Date();
//    	  var h = today.getHours();
//    	  var m = today.getMinutes();
//    	  var s = today.getSeconds();
//          h = this.checkTime(h);
//    	  m = this.checkTime(m);
//    	  s = this.checkTime(s);
//    	  var time = h + ":" + m + ":" + s;
//    	  return time;
//    	},
//    checkTime: function (i) {
//        if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
//    	return i;
//    }
});

});
