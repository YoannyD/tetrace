# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import logging
import calendar
import pytz

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    @api.depends('allocation_ids.state')
    def _compute_allocation_count(self):
        for obj in self:
            obj.allocation_count = len(obj.allocation_ids)
            count = 0
            for allocation in obj.allocation_ids:
                if allocation.state in ['allocated']:
                    count += 1
            obj.allocation_open_count = count

    @api.depends('warranty_period', 'purchase_date')
    def get_warranty_last_date(self):
        for obj in self:
            if obj.purchase_date:
                if obj.warranty_period:
                    obj.warranty_date = obj.purchase_date + relativedelta(months=obj.warranty_period, days=-1)
                else:
                    obj.warranty_date = obj.purchase_date
            else:
                obj.warranty_date = False

    def name_get(self):
        result = []
        for record in self:
            if record.name and record.serial_no and record.partner_ref:
                result.append(
                    (record.id, record.name + '/' + record.serial_no + '/' + record.partner_ref))
            elif record.name and record.partner_ref and not record.serial_no:
                result.append(
                    (record.id, record.name + '/' + record.partner_ref))
            elif record.name and record.serial_no and not record.partner_ref:
                result.append(
                    (record.id, record.name + '/' + record.serial_no))
            elif record.name and not record.serial_no:
                result.append((record.id, record.name))
        return result

    product_id = fields.Many2one(
        'product.product', string='Main Product', required=True, domain="[('type', '=', 'product')]")
    allocation_ids = fields.One2many('allocation.request', 'equipment_id', string="Allocation Request")
    allocation_count = fields.Integer(
        compute='_compute_allocation_count', string="Allocation Count")
    allocation_open_count = fields.Integer(
        compute='_compute_allocation_count', string="Current Allocation")
    state = fields.Selection(
        [('available', 'Available'), ('not-available', 'Not Available')],
        string="State", default="available")
    owner_user_id = fields.Many2one(
        'res.users', string='Owner', tracking=True, readonly=False)
    purchase_date = fields.Date(string="Purchase Date", tracking=True)
    warranty_period = fields.Integer(string="Warranty Period")
    warranty_date = fields.Date('Warranty', compute="get_warranty_last_date", store=True)

    @api.onchange('equipment_assign_to')
    def _onchange_equipment_assign_to(self):
        if self.equipment_assign_to == 'employee':
            self.department_id = False
        if self.equipment_assign_to == 'department':
            self.owner_user_id = False
        if self.equipment_assign_to == 'other':
            self.department_id = False
            self.owner_user_id = False
        self.assign_date = fields.Date.context_today(self)

    @api.depends('employee_id', 'department_id', 'equipment_assign_to')
    def _compute_owner(self):
        self.owner_user_id = self.env.user.id
        if self.equipment_assign_to == 'employee':
            self.owner_user_id = self.employee_id.user_id.id
        elif self.equipment_assign_to == 'department':
            self.owner_user_id = self.department_id.sudo().manager_id.user_id.id
        elif self.equipment_assign_to == 'other':
            self.owner_user_id = False

    @api.model
    def create(self, vals):
        if vals.get('warranty_period', True) < 0:
            raise UserError(
                _('Warranty Period of an Equipment must be greater than or equal to 0.'))
        return super(MaintenanceEquipment, self).create(vals)

    def write(self, vals):
        if vals.get('warranty_period', True) < 0:
            raise UserError(
                _('Warranty Period of an Equipment must be greater than or equal to 0.'))
        return super(MaintenanceEquipment, self).write(vals)


class AllocationRequest(models.Model):
    _name = "allocation.request"
    _inherit = ['mail.thread']
    _description = 'Allocation Requests'
    _order = "id desc"

    def unlink(self):
        for record_obj in self:
            if record_obj.state != 'cancel':
                raise UserError(
                    _("You can ONLY delete the Request(s) that are in cancelled state !!!"))
        return super(AllocationRequest, self).unlink()

    def get_sign_in_time(self, sign_in):
        utc = pytz.utc
        current_timezone = 'Asia/Kolkata'
        local_timezone = pytz.timezone(current_timezone)
        now = datetime.today().replace(tzinfo=utc).astimezone(local_timezone).replace(tzinfo=None)
        dif = now - datetime.now()
        time_start = sign_in + dif
        return time_start + timedelta(seconds=1)

    def get_date(self, sign_in):
        return self.get_sign_in_time(sign_in).strftime('%d-%m-%Y')

    def get_time(self, sign_in):
        return self.get_sign_in_time(sign_in).strftime('%H:%M:%S')

    @api.model
    def get_default_department(self):
        if self.request_user_id and self.request_user_id.sudo().employee_ids:
            if self.request_user_id.sudo().employee_ids[0].department_id:
                return self.request_user_id.sudo().employee_ids[0].department_id.id
        else:
            user = self.env['res.users'].browse(self._uid)
            if user.sudo().employee_ids and user.sudo().employee_ids[0].department_id:
                return user.sudo().employee_ids[0].department_id.id
        return False

    @api.model
    def get_equipment_id_domain(self):
        department_id = self.get_default_department()
        if not self.env.user._is_admin():
            if not department_id:
                raise UserError(
                    _("Employee Department not set. Please contact Hr Department."))
        equipment_ids = []
        if self.category_id:
            equipment_ids += self.env['maintenance.equipment'].search(
                [('category_id', '=', self.category_id.id),
                 ('department_id', '=', department_id)]).ids
            equipment_ids += self.env['maintenance.equipment'].search(
                [('category_id', '=', self.category_id.id),
                 ('owner_user_id', '=', False), ('department_id', '=', False)]).ids
        return equipment_ids

    @api.depends('category_id', 'request_user_id')
    def equipment_domain(self):
        for obj in self:
            obj.equipment_ids = [(6, 0, obj.get_equipment_id_domain())]

    @api.model
    def get_user_domain(self):
        groups = self.env['res.users'].browse(self._uid).groups_id.ids
        manager_group = self.env['ir.model.data'].get_object_reference(
            'equipment_allocations', 'group_equipment_user')[1]
        if manager_group not in groups:
            users = []
            employees = self.env['hr.employee'].sudo().search(
                [('department_id', '=', self.get_default_department())])
            for employee in employees:
                if employee.user_id:
                    users.append(employee.user_id.id)
            return users
        return self.env["res.users"].sudo().search([('employee_ids', '!=', False)]).ids

    name = fields.Char('Subjects', required=True, tracking=True)
    description = fields.Text('Description')
    request_date = fields.Datetime(
        'Request Date', tracking=True,
        default=fields.Datetime.now,
        help="Requested date for the Allocation.", copy=False, readonly=True,
        states={'new': [('readonly', False)]}, required=True)
    request_user_id = fields.Many2one(
        'res.users', string='Allocated To', default=lambda s: s.env.uid,
        tracking=True, copy=False, readonly=True,
        states={'new': [('readonly', False)]}, required=True,
        domain=lambda self: [('id', 'in', self.get_user_domain())])
    approved_by = fields.Many2one(
        'res.users', string='Approved By', tracking=True, copy=False)
    return_to = fields.Many2one(
        'res.users', string='Return To', tracking=True, copy=False)
    rejected_by = fields.Many2one(
        'res.users', string='Rejected By', tracking=True, copy=False)
    category_id = fields.Many2one('maintenance.equipment.category',
                                  string='Category', required=True,
                                  readonly=True,
                                  states={'new': [('readonly', False)]})
    equipment_id = fields.Many2one(
        'maintenance.equipment', string='Equipment', index=True, copy=False,
        domain="[('id', 'in', equipment_ids)]", readonly=True,
        states={'new': [('readonly', False)]})
    product_id = fields.Many2one('product.product',
                                 related='equipment_id.product_id',
                                 string='Product', store=True, readonly=True)
    equipment_ids = fields.Many2many("maintenance.equipment", 'request_id',
                                     'equipment_id',
                                     compute="equipment_domain",
                                     string="Equipments")
    state = fields.Selection([
        ('new', 'New'), ('approved', 'Approved'),
        ('allocated', 'Allocated'), ('returned', 'Returned'),
        ('cancel', 'Cancelled')], string='Stage',
        tracking=True, default='new', copy=False)
    priority = fields.Selection(
        [('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'),
         ('3', 'High')], string='Priority', default=0)
    color = fields.Integer('Color Index')
    close_date = fields.Datetime(
        'Return Date', help="Date on which the allocated equipment has been returned.", copy=False)
    archive = fields.Boolean(
        default=False, copy=False,
        help="Set archive to true to hide the Allocation request without deleting it.")
    duration = fields.Float(
        help="Duration in hours and minutes.", copy=False)
    type = fields.Selection(
        [('on-demand', 'On-demand'), ('permanent', 'Permanent')],
        string="Allocation Type", default="on-demand",
        help="The current allocation of the equipment belongs to: \n"
        "- On-demand: Available when needed. Employee request for an equipment for a short or particular duration of time.\n"
        "- Permanent: The Equipment permanently get allocated to the employee.\n",
        readonly=True, states={'new': [('readonly', False)]}, copy=False)

    @api.onchange('category_id', 'request_user_id')
    def onchange_category_id(self):
        self.equipment_id = False
        equipment_ids = self.get_equipment_id_domain()
        return {'domain': {'equipment_id': [('id', 'in', equipment_ids)]}}

    @api.model
    def create(self, vals):
        today = datetime.strftime(datetime.now(), '%Y-%m-%d')
        if not vals.get('type'):
            vals.update({'type': 'on-demand'})
        if vals.get('type') == 'on-demand':
            if vals.get('request_date') and vals.get('request_date') < today:
                raise UserError(_(
                    "Scheduled date for an equipment request must be of future."))
        res = super(AllocationRequest, self).create(vals)
        res.get_equipment_id_domain()
        res.message_subscribe(
            partner_ids=res.category_id.message_partner_ids.ids+[res.request_user_id.partner_id.id])
        template = self.env['ir.model.data'].xmlid_to_object(
            'equipment_allocations.email_equipment_allocation_request')
        Template = self.env['mail.template']
        if res.type == "on-demand":
            if template:
                # template.send_mail(res.id, True)
                partner = []
                template = template.get_email_template(res.id)
                body_html = Template.with_context(template._context)._render_template(
                    template.body_html, 'allocation.request', res.id)
                subject_html = Template.with_context(template._context)._render_template(
                    template.subject, 'allocation.request', res.id)
                res.message_post(
                    body=body_html,
                    subject=subject_html,
                    subtype='mail.mt_comment',
                    partner_ids=res.category_id.technician_user_id.partner_id.ids + partner + res.category_id.message_partner_ids.ids,
                    message_type='comment',
                    email_from= "no-reply@webkul.com"
                )
        return res

    def message_get_message_notify_values(self, message, message_values):
        """ Override to avoid keeping all notified recipients of a comment.
        We avoid tracking needaction on post comments. Only emails should be
        sufficient. """
        if message.message_type == 'comment':
            return {
                'needaction_partner_ids': [],
            }
        return {}

    def write(self, vals):
        today = datetime.strftime(datetime.now(), '%Y-%m-%d')
        for obj in self:
            if vals.get('state'):
                if vals.get('state') in ["cancel"]:
                    if obj.state not in ['new', 'approved', 'allocated']:
                        raise UserError(
                            _("Sorry, you can't cancel those request which are in 'Allocated' and 'Returned' state."))
                    else:
                        if self._context.get('cancel'):
                            vals.update({'rejected_by': self._uid})
                        else:
                            raise UserError(
                                _("Sorry, you can't cancel this record because no reason is mentioned"))
                elif vals.get('state') in ['approved']:
                    if not self.check_authority():
                        raise UserError(
                            _("Sorry, You don't have access to Approve any request."))
                    if obj.state not in ['new']:
                        raise UserError(
                            _("Sorry, you can approve only those requests which are in 'New' state."))
                    else:
                        if not obj.equipment_id:
                            raise UserError(
                                _("Firstly, please select a Equipment."))
                        if self.check_equipment_availablity():
                            if not self._context.get('approved'):
                                raise UserError(_("Test"))
                        vals.update({'approved_by': self._uid})
                elif vals.get('state') in ['allocated']:
                    if not self.check_authority():
                        raise UserError(
                            _("Sorry, You don't have access to Allocate any request."))
                    if obj.state not in ['approved']:
                        raise UserError(
                            _("Sorry, you can allocate only those requests which are in 'Approved' state."))
                    else:
                        if not obj.request_date:
                            vals.update({'request_date': datetime.now()})
                elif vals.get('state') == 'new':
                    if obj.state not in ['cancel', 'returned']:
                        raise UserError(
                            _("Sorry, you can't move this request to 'New' state."))
                elif vals.get('state') == 'returned':
                    if not self.check_authority():
                        raise UserError(
                            _("Sorry, You don't have access to Return any request."))
                    if obj.state not in ['allocated']:
                        raise UserError(
                            _("You can return only those requests which are Allocated."))
                    else:
                        total_seconds = datetime.now() - obj.request_date
                        vals.update({'return_to': self._uid,
                                     'close_date': datetime.now(),
                                     'duration': total_seconds.total_seconds() / 3600})
        res = super(AllocationRequest, self).write(vals)
        for obj in self:
            Template = self.env['mail.template']
            user_email = self.env['res.users'].browse(self._uid).email
            if vals.get('request_date'):
                if obj.type == 'on-demand' and vals.get('request_date') < today:
                    raise UserError(_(
                        "Scheduled date for an equipment request must be of future. "))
            if vals.get('state'):
                if obj.state in ["cancel", 'returned']:
                    obj.release_equipment()
                    if obj.state == 'cancel':
                        cancel_template = self.env['ir.model.data'].xmlid_to_object(
                        'equipment_allocations.email_allocation_cancel')
                        if cancel_template:
                            subject_html = "Your Request for %s has been cancelled"%obj.category_id.name
                            cancel_template = cancel_template.get_email_template(obj.id)
                            body_html = Template.with_context(cancel_template._context)._render_template(
                                cancel_template.body_html, 'allocation.request', obj.id)
                            if obj.type == "permanent" and not self._context.get('replace_equipment'):
                                subject_html = obj.equipment_id.display_name + \
                                    " has been allocated to you permanently"
                            _logger.info('=============%r',subject_html)
                            if subject_html:
                                obj.message_post(
                                    body=body_html,
                                    subject=subject_html,
                                    subtype='mail.mt_comment',
                                    message_type='comment',
                                )
                if obj.state in ['approved', 'allocated']:
                    obj.allocate_resource()
                    template = self.env['ir.model.data'].xmlid_to_object(
                        'equipment_allocations.email_equipment_allocation_approve')
                    if template:
                        template = template.get_email_template(obj.id)
                        body_html = Template.with_context(template._context)._render_template(
                            template.body_html, 'allocation.request', obj.id)
                        if obj.state == "approved":
                            if obj.type == "on-demand":
                                subject_html = Template.with_context(template._context)._render_template(
                                    template.subject, 'allocation.request', obj.id)
                                obj.message_post(body=body_html,
                                                 subject=subject_html,
                                                 subtype='mail.mt_comment',
                                                 partner_ids=obj.request_user_id.partner_id.ids,
                                                 message_type='comment',
                                                 email_from= user_email
                                                 )
                        if obj.state == "allocated":
                            if obj.type == "on-demand":
                                subject_html = obj.equipment_id.display_name + \
                                    " has been allocated to you."
                            if obj.type == "permanent" and not self._context.get('replace_equipment'):
                                subject_html = obj.equipment_id.display_name + \
                                    " has been allocated to you permanently"
                            if subject_html:
                                obj.message_post(
                                    body=body_html,
                                    subject=subject_html,
                                    subtype='mail.mt_comment',
                                    partner_ids=obj.request_user_id.partner_id.ids,
                                    message_type='comment',
                                    email_from= user_email
                                )

        return res

    def check_authority(self):
        groups = self.env['res.users'].browse(self._uid).groups_id.ids
        manager_group = self.env['ir.model.data'].get_object_reference(
            'equipment_allocations', 'group_equipment_user')[1]
        if manager_group not in groups:
            return False
        return True

    def check_allowed_equipment(self):
        msg = ""
        request_id = False
        if self.state == "new":
            request_id = self.search(
                [('equipment_id', '=', self.equipment_id.id),
                 ('state', 'in', ['approved'])], limit=1)
            msg = 'This equipment is currently approved for <b>(%s)</b> request. <br/>' \
                  '<i class="fa fa-hand-o-right text-danger" aria-hidden="true"/> ' \
                  '<b> Note :</b> You cannot allocate the same equipment to multiple requests.<br/> ' \
                  'So, If you want to <b>%s</b> the previous approved request and <b>Approve</b> ' \
                  'the current request then click on <b>"Update Now"</b> button else click on <b>"Cancel"</b>.'
            if request_id:
                msg = msg % (request_id.display_name, 'Cancel')
            else:
                request_id = self.search(
                    [('equipment_id', '=', self.equipment_id.id), ('state', 'in', ['allocated'])], limit=1)
                if request_id:
                    msg = msg % (request_id.display_name, 'Return')
                else:
                    return True
        wizard_id = self.env['request.allocated.wizard'].create(
            {'message': msg})
        return {
            'name': "Message",
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'request.allocated.wizard',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
        }

    def check_equipment_availablity(self):
        if self.equipment_id.state != 'available':
            request_id = self.search([
                ('equipment_id', '=', self.equipment_id.id),
                ('state', 'in', ['approved', 'allocated'])
            ])
            return request_id
        return False

    def release_equipment(self):
        for obj in self:
            if obj.equipment_id.state == "not-available":
                obj.sudo().equipment_id.state = "available"

    def allocate_resource(self):
        for obj in self:
            if obj.equipment_id.state == "available":
                obj.equipment_id.sudo().state = "not-available"

    def set_approved(self):
        for obj in self:
            if not obj.equipment_id:
                raise UserError(
                    _("Firstly, please select an Equipment."))
            if obj.state == "new":
                if obj.equipment_id.state == 'available':
                    obj.state = 'approved'
                else:
                    return obj.check_allowed_equipment()
            else:
                raise UserError(
                    _("Sorry, you can approve only request which are in 'New' state."))

    def set_allocated(self):
        for obj in self:
            if obj.state == "approved":
                obj.state = 'allocated'
                if obj.type == "permanent":
                    obj.sudo().equipment_id.equipment_assign_to = 'employee'
                    obj.sudo().equipment_id.owner_user_id = obj.request_user_id
            else:
                raise UserError(
                    _("Sorry, Allocated only those request which are in Approved."))

    def set_draft(self):
        for obj in self:
            if obj.state in ["cancel", 'returned']:
                obj.state = 'new'

    def set_returned(self):
        for obj in self:
            if obj.state == "allocated":
                obj.state = 'returned'
                if obj.type == "permanent":
                    obj.equipment_id.equipment_assign_to = "other"
                    obj.equipment_id.owner_user_id = False
            else:
                raise UserError(
                    _("Sorry, you can return only those request which are Allocated."))

    def set_cancel(self):
        for obj in self:
            if obj.state in ['new', 'approved']:
                obj.state = 'cancel'
            else:
                raise UserError(
                    _("Sorry, you can cancel only those request which are in 'New and Approved' state."))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_equipment_count(self):
        for obj in self:
            obj.equipment_counts = self.env['maintenance.equipment'].search_count(
                [('product_id', '=', obj.id)])

    equipment_counts = fields.Integer(compute="get_equipment_count")
