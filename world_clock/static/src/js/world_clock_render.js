odoo.define('world_clock.removetimer', function (require) {
var EditorMenu = require('website.editor.menu');
var websiteNavbarData = require('website.navbar');

    // Detect Edit mode and remove timer.
  var EditPageRemoveTimer = websiteNavbarData.WebsiteNavbarActionWidget.extend({
        xmlDependencies: ['/website/static/src/xml/website.editor.xml','/world_clock/static/src/xml/snippets.xml'],
       /**
         * @override
        */
       actions: _.extend({}, websiteNavbarData.WebsiteNavbarActionWidget.prototype.actions, {
            edit: '_startEditMode',
       }),

       template: "world_clock.world_clock_template",

       init: function(){
            this._super.apply(this, arguments);
       },

        _startEditMode: function () {
            if(self.$el){
            if(self.$el.find('#removeWorld').length != 0)
                self.$el.find('#removeWorld').remove();
                }
        },

    });
    websiteNavbarData.websiteNavbarRegistry.add(EditPageRemoveTimer, '#edit-page-menu');
});
odoo.define('world_clock.world_clock_render', function (require) {
'use strict';
var core = require('web.core');
var ajax = require('web.ajax');
var utils = require('web.utils');
var publicWidget = require('web.public.widget');
var qweb = core.qweb;

publicWidget.registry.clockRender = publicWidget.Widget.extend({
    selector: '.world_clock_template',
    xmlDependencies: ['/world_clock/static/src/xml/snippets.xml'],
    start: function () {
        self = this
            this._rpc({
                route: '/render_content',
            }).then(function (result) {
                if (result) {
                       self.$el.append(qweb.render('world_clock.list',{'world_clock_obj':result.world_clock_obj})).ready(()=>{
                         self._startTimeCounter(result.world_clock_obj)
                       })
                }
            });

        return this._super.apply(this, arguments);
    },

     _getDuration: function (dateStart, duration) {
        if (dateStart) {
            return dateStart.add(duration,'seconds');
        }
        else return 0;
    },
    _startTimeCounter: function () {
        self = this;
        this.$el.find('.world_clock_template').find('.tzDateVal').each(function(i) {
            var selfLoop = $(this);
            clearTimeout(self.tzDate);
            if (selfLoop.text()) {
                self.tzDate = setTimeout(function () {
                    self._startTimeCounter();
                }, 1000);
                selfLoop.text(moment.utc(self._getDuration(moment.utc(selfLoop.text()), 1)).format("dddd, MMMM-DD-YYYY hh:mm:ss A"));
            }
            else{
                clearTimeout(self.tzDate);
            }
        })
    },
});

return publicWidget.registry.world_clock_render;

});
