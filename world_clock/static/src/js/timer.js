odoo.define('world_clock.timer', function (require) {
"use strict";

var fieldRegistry = require('web.field_registry');
var AbstractField = require('web.AbstractField');

var TimerFieldWidget = AbstractField.extend({

    /**
     * @override
     * @private
     */
    isSet: function () {
        return true;
    },
    /**
     * @private
     */
    _getDuration: function (dateStart, duration) {
        if (dateStart) {
            return dateStart.add(duration,'seconds');
        }
        else return 0;
    },
    /**
     * @override
     * @private
     */
    _render: function () {
        this._startTimeCounter();

    },
    /**
     * @override
     */
    destroy: function () {
        this._super.apply(this, arguments);
        clearTimeout(this.timer);
    },
    /**
     * @private
     */
    _startTimeCounter: function () {
        var self = this;
        clearTimeout(this.tzDate);
        if (self.record.data.tzDate) {
            this.tzDate = setTimeout(function () {
                self._startTimeCounter();
            }, 1000);
            this.$el.text(moment.utc(self._getDuration(self.record.data.tzDate, 1)).format("dddd, MMMM-DD-YYYY hh:mm:ss A"));
        }
        else{
            clearTimeout(this.tzDate);
        }
    },
});

fieldRegistry.add('global_datetime', TimerFieldWidget);

});
