odoo.define('tetrace.GanttRow', function (require) {
    'use strict';
    var GanttRow = require('web_gantt.GanttRow');
    var core = require('web.core');
    var _t = core._t;

    GanttRow.include({
        _insertIntoSlot: function () {
            var self = this;
            var scale = this.state.scale;
            var intervalToken = this.SCALES[scale].interval;
            var precision = this.viewInfo.activeScaleInfo.precision;
            var x, y;
            this.slots = _.map(this.viewInfo.slots, function (date, key) {
                var slotStart = date;
                var slotStop = date.clone().add(1, intervalToken);
                var slotHalf = moment((slotStart + slotStop) / 2);
                var slotUnavailability;
                var morningUnavailabilities = 0; //morning hours unavailabilities
                var afternoonUnavailabilities = 0; //afternoon hours unavailabilities
                self.unavailabilities.forEach(function (unavailability) {
                    if (unavailability.start < slotStop && unavailability.stop > slotStart) {
                        if ((scale === 'month' || scale === 'week')) {
                            // We can face to 3 different cases and we will compute the sum
                            // of all unavailability periods for the morning and the afternoon:
                            //
                            // slotStart                slotHalf            slotStop
                            //    |      ______________     :                   |
                            // 1. |     |______________|    :                   |
                            //    |                         :    ___________    |
                            // 2. |                         :   |___________|   |
                            //    |                 ________:_______            |
                            // 3. |                |________:_______|           |
                            //    |                         :                   |
                            //    |                         :                   |
                            x = unavailability.start.diff(slotHalf) / (3600 * 1000);
                            y = unavailability.stop.diff(slotHalf) / (3600 * 1000);
                            if (x < 0 && y < 0) { // Case 1.
                                morningUnavailabilities += Math.min(-x, 12) - Math.min(-y, 12);
                            } else if (x > 0 && y > 0) { // Case 2.
                                afternoonUnavailabilities += Math.min(y, 12) - Math.min(x, 12);
                            } else { // Case 3.
                                morningUnavailabilities += Math.min(-x, 12);
                                afternoonUnavailabilities += Math.min(y, 12);
                            }
                        } else {
                            slotUnavailability = 'full';
                        }
                    }
                });
                if (scale === 'month' || scale === 'week') {
                    if ((morningUnavailabilities > 10 && afternoonUnavailabilities > 10) || (precision !== 'half' && morningUnavailabilities + afternoonUnavailabilities > 22)) {
                        slotUnavailability = 'full';
                    } else if (morningUnavailabilities > 10 && precision === 'half') {
                        slotUnavailability = 'first_half';

                    } else if (afternoonUnavailabilities > 10 && precision === 'half') {
                        slotUnavailability = 'second_half';
                    }
                }
                return {
                    isToday: date.isSame(new Date(), 'day') && self.state.scale !== 'day',
                    unavailability: slotUnavailability,
                    hasButtons: !self.isGroup && !self.isTotal,
                    start: slotStart,
                    stop: slotStop,
                    pills: [],
                };
            });
            var slotsToFill = this.slots;
            this.pills.forEach(function (currentPill) {
                var skippedSlots = [];
                slotsToFill.some(function (currentSlot) {
                    var start_date = currentPill.startDate
                    var fitsInThisSlot = start_date < currentSlot.stop;
                    if (self.state.scale === 'year') {
                        var b = start_date.clone().add(1, 'month');
                        fitsInThisSlot = b < currentSlot.stop;
                    }
                    if (fitsInThisSlot) {
                        currentSlot.pills.push(currentPill);
                    } else {
                        skippedSlots.push(currentSlot);
                    }
                    return fitsInThisSlot;
                });
                // Pills are sorted by start date, so any slot that was skipped
                // for this pill will not be suitable for any of the next pills
                slotsToFill = _.difference(slotsToFill, skippedSlots);
            });
        },
    });
});