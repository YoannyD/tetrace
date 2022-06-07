odoo.define('tetrace.GanttRenderer', function (require) {
    'use strict';
    var GanttRenderer = require('web_gantt.GanttRenderer');
    var pyUtils = require('web.py_utils');
    var core = require('web.core');
    var _t = core._t;

    GanttRenderer.include({
        _getSlotsDates: function () {
            var token = this.SCALES[this.state.scale].interval;
            var stopDate = this.state.stopDate;
            var day = this.state.startDate;
            var dates = [];
            while (day <= stopDate) {
                dates.push(day);
                day = day.clone().add(1, token);
            }
            return dates;
        },
    });
});