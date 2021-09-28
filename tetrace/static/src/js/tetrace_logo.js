odoo.define('tetrace.TetraceLogo', function (require) {
"use strict";
    
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    
    var TetraceLogo = Widget.extend({
        template: "WebClient.TetraceLogo",
        xmlDependencies: ['/tetrace/static/src/xml/tetrace_logo.xml'],
    });
    
    SystrayMenu.Items.push(TetraceLogo);
});