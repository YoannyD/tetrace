# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import re

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_repr
from datetime import datetime, timedelta
from odoo.tests.common import Form
from odoo.tools import exception_to_unicode

from odoo.exceptions import ValidationError, UserError
from odoo.addons.tetrace.models.conexion_mysql import ConexionMysql

_logger = logging.getLogger(__name__)

CODIGOS_SII = [
    ('33', _('Factura electrónica')),
    ('34', _('Factura no afecta o exenta electrónica')),
    ('56', _('Nota de débito electrónica')),
    ('61', _('Nota de crédito electrónica'))
]

DEFAULT_FACTURX_DATE_FORMAT = '%Y%m%d'


class AccountMove(models.Model):
    _inherit = "account.move"
    _state_to = ["posted"]

    def _default_validacion_id(self):
        validacion = self.env['tetrace.validacion_user'].search([
            ('user_id', '=', self.env.user.id),
            ('validacion_id', '!=', False)
        ], limit=1)
        if validacion:
            return validacion.id
        return None

    asiento_anticipo_id = fields.Many2one('account.move', domain=[('type', '=', 'entry')], string="Asiento anticipo")
    fecha_vencimiento_anticipo = fields.Date("Fecha vencimiento anticipo",
                                             compute="_compute_fecha_vencimiento_anticipo")
    incoterm_complemento = fields.Char('Complemento Incoterm', translate=True)
    secuencia_num = fields.Integer('Número secuencia')
    secuencia = fields.Char('Secuencia')
    nomina_id = fields.Many2one('tetrace.nomina', string="Nómina")
    validacion_id = fields.Many2one('tetrace.validacion_user', string="Validación",
                                    default=lambda self: self._default_validacion_id())
    validacion_baremo = fields.Boolean(related="validacion_id.validacion_id.baremo")
    tickelia_id = fields.Many2one('tetrace.tickelia', string="Tickelia")
    codigo_sii = fields.Selection(CODIGOS_SII, string="Código SII")
    fecha_servicio = fields.Date("Fecha servicio")
    importe_validacion_euros = fields.Monetary("Importe validación en euros", store=True,
                                               compute="_compute_importe_validacion_euros")
    sale_order_id = fields.Many2one("sale.order", compute="_compute_sale_order_id", store=True)
    invoice_line_cambia = fields.Char("Líneas de factura cambiadas")
    baremo = fields.Boolean("Fuera Baremo")
    lineas_actualizadas = fields.Integer("Líneas actualizadas")
    tipo_proyecto_id = fields.Many2one("tetrace.tipo_proyecto", string="Tipo proyecto")

    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        res = super(AccountMove, self)._onchange_purchase_auto_complete() or {}
        if 'warning' in res and (res['warning']['message'] == _("Selected purchase order have different payment mode.") or \
                                res['warning']['message'] == _("Selected purchase order have different supplier bank.")):
            del res['warning']
        return res
    
    @api.depends("invoice_origin")
    def _compute_sale_order_id(self):
        for r in self:
            if r.type not in ['out_invoice', 'out_refund', 'out_receipt']:
                continue
            
            if r.invoice_origin:
                for origin in r.invoice_origin.split(","):
                    sale_order = self.env['sale.order'].search([('name', '=', origin.strip())], limit=1)
                    if sale_order:
                        r.sale_order_id = sale_order.id
                        return
            else:
                r.sale_order_id = False
    
    def extraer_numero_factura(self):
        #Devolvemos el numero de factura que se encuentra en la descripción de las líneas
        for r in self:
            for line in r.line_ids:
                resultado = re.search(r"[A-Z]*[0-9]{4}/[0-9]{3}", line.name)
                if resultado:
                    return resultado.group(0)
                    break    

    def _import_facturx_invoice(self, tree):
        ###################################################
        ##################Ingetive#########################
        ###################################################
        #Modificamos original odoo/addons/account_facturx##
        #Añadimos cuenta analítica por defecto del partner#
        ###################################################
        ##################Ingetive#########################
        ###################################################
        ''' Extract invoice values from the Factur-x xml tree passed as parameter.

        :param tree: The tree of the Factur-x xml file.
        :return: A dictionary containing account.invoice values to create/update it.
        '''
        amount_total_import = None

        default_type = False
        if self._context.get('default_journal_id'):
            journal = self.env['account.journal'].browse(self.env.context['default_journal_id'])
            default_type = 'out_invoice' if journal.type == 'sale' else 'in_invoice'
        elif self._context.get('default_type'):
            default_type = self._context['default_type']
        elif self.type in self.env['account.move'].get_invoice_types(include_receipts=True):
            # in case an attachment is saved on a draft invoice previously created, we might
            # have lost the default value in context but the type was already set
            default_type = self.type

        if not default_type:
            raise UserError(_("No information about the journal or the type of invoice is passed"))
        if default_type == 'entry':
            return

        # Total amount.
        elements = tree.xpath('//ram:GrandTotalAmount', namespaces=tree.nsmap)
        total_amount = elements and float(elements[0].text) or 0.0

        # Refund type.
        # There is two modes to handle refund in Factur-X:
        # a) type_code == 380 for invoice, type_code == 381 for refund, all positive amounts.
        # b) type_code == 380, negative amounts in case of refund.
        # To handle both, we consider the 'a' mode and switch to 'b' if a negative amount is encountered.
        elements = tree.xpath('//rsm:ExchangedDocument/ram:TypeCode', namespaces=tree.nsmap)
        type_code = elements[0].text

        default_type.replace('_refund', '_invoice')
        if type_code == '381':
            default_type = 'out_refund' if default_type == 'out_invoice' else 'in_refund'
            refund_sign = -1
        else:
            # Handle 'b' refund mode.
            if total_amount < 0:
                default_type = 'out_refund' if default_type == 'out_invoice' else 'in_refund'
            refund_sign = -1 if 'refund' in default_type else 1

        # Write the type as the journal entry is already created.
        self.type = default_type

        # self could be a single record (editing) or be empty (new).
        with Form(self.with_context(default_type=default_type)) as invoice_form:
            # Partner (first step to avoid warning 'Warning! You must first select a partner.').
            partner_type = invoice_form.journal_id.type == 'purchase' and 'SellerTradeParty' or 'BuyerTradeParty'
            elements = tree.xpath('//ram:'+partner_type+'/ram:SpecifiedTaxRegistration/ram:ID', namespaces=tree.nsmap)
            partner = elements and self.env['res.partner'].search([('vat', '=', elements[0].text)], limit=1)
            if not partner:
                elements = tree.xpath('//ram:'+partner_type+'/ram:Name', namespaces=tree.nsmap)
                partner_name = elements and elements[0].text
                partner = elements and self.env['res.partner'].search([('name', 'ilike', partner_name)], limit=1)
            if not partner:
                elements = tree.xpath('//ram:'+partner_type+'//ram:URIID[@schemeID=\'SMTP\']', namespaces=tree.nsmap)
                partner = elements and self.env['res.partner'].search([('email', '=', elements[0].text)], limit=1)
            if partner:
                invoice_form.partner_id = partner

            # Reference.
            elements = tree.xpath('//rsm:ExchangedDocument/ram:ID', namespaces=tree.nsmap)
            if elements:
                invoice_form.ref = elements[0].text

            # Name.
            elements = tree.xpath('//ram:BuyerOrderReferencedDocument/ram:IssuerAssignedID', namespaces=tree.nsmap)
            if elements:
                invoice_form.invoice_payment_ref = elements[0].text

            # Comment.
            elements = tree.xpath('//ram:IncludedNote/ram:Content', namespaces=tree.nsmap)
            if elements:
                invoice_form.narration = elements[0].text

            # Total amount.
            elements = tree.xpath('//ram:GrandTotalAmount', namespaces=tree.nsmap)
            if elements:

                # Currency.
                if elements[0].attrib.get('currencyID'):
                    currency_str = elements[0].attrib['currencyID']
                    currency = self.env.ref('base.%s' % currency_str.upper(), raise_if_not_found=False)
                    if currency != self.env.company.currency_id and currency.active:
                        invoice_form.currency_id = currency

                    # Store xml total amount.
                    amount_total_import = total_amount * refund_sign

            # Date.
            elements = tree.xpath('//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString', namespaces=tree.nsmap)
            if elements:
                date_str = elements[0].text
                date_obj = datetime.strptime(date_str, DEFAULT_FACTURX_DATE_FORMAT)
                invoice_form.invoice_date = date_obj.strftime(DEFAULT_SERVER_DATE_FORMAT)

            # Due date.
            elements = tree.xpath('//ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString', namespaces=tree.nsmap)
            if elements:
                date_str = elements[0].text
                date_obj = datetime.strptime(date_str, DEFAULT_FACTURX_DATE_FORMAT)
                invoice_form.invoice_date_due = date_obj.strftime(DEFAULT_SERVER_DATE_FORMAT)

            # Invoice lines.
            elements = tree.xpath('//ram:IncludedSupplyChainTradeLineItem', namespaces=tree.nsmap)
            if elements:
                for element in elements:
                    with invoice_form.invoice_line_ids.new() as invoice_line_form:

                        # Sequence.
                        line_elements = element.xpath('.//ram:AssociatedDocumentLineDocument/ram:LineID', namespaces=tree.nsmap)
                        if line_elements:
                            invoice_line_form.sequence = int(line_elements[0].text)

                        # Product.
                        line_elements = element.xpath('.//ram:SpecifiedTradeProduct/ram:Name', namespaces=tree.nsmap)
                        if line_elements:
                            invoice_line_form.name = line_elements[0].text
                        line_elements = element.xpath('.//ram:SpecifiedTradeProduct/ram:SellerAssignedID', namespaces=tree.nsmap)
                        if line_elements and line_elements[0].text:
                            product = self.env['product.product'].search([('default_code', '=', line_elements[0].text)])
                            if product:
                                invoice_line_form.product_id = product
                        if not invoice_line_form.product_id:
                            line_elements = element.xpath('.//ram:SpecifiedTradeProduct/ram:GlobalID', namespaces=tree.nsmap)
                            if line_elements and line_elements[0].text:
                                product = self.env['product.product'].search([('barcode', '=', line_elements[0].text)])
                                if product:
                                    invoice_line_form.product_id = product

                        # Quantity.
                        line_elements = element.xpath('.//ram:SpecifiedLineTradeDelivery/ram:BilledQuantity', namespaces=tree.nsmap)
                        if line_elements:
                            invoice_line_form.quantity = float(line_elements[0].text)

                        # Price Unit.
                        line_elements = element.xpath('.//ram:GrossPriceProductTradePrice/ram:ChargeAmount', namespaces=tree.nsmap)
                        if line_elements:
                            quantity_elements = element.xpath('.//ram:GrossPriceProductTradePrice/ram:BasisQuantity', namespaces=tree.nsmap)
                            if quantity_elements:
                                invoice_line_form.price_unit = float(line_elements[0].text) / float(quantity_elements[0].text)
                            else:
                                invoice_line_form.price_unit = float(line_elements[0].text)
                        else:
                            line_elements = element.xpath('.//ram:NetPriceProductTradePrice/ram:ChargeAmount', namespaces=tree.nsmap)
                            if line_elements:
                                quantity_elements = element.xpath('.//ram:NetPriceProductTradePrice/ram:BasisQuantity', namespaces=tree.nsmap)
                                if quantity_elements:
                                    invoice_line_form.price_unit = float(line_elements[0].text) / float(quantity_elements[0].text)
                                else:
                                    invoice_line_form.price_unit = float(line_elements[0].text)
                        # Discount.
                        line_elements = element.xpath('.//ram:AppliedTradeAllowanceCharge/ram:CalculationPercent', namespaces=tree.nsmap)
                        if line_elements:
                            invoice_line_form.discount = float(line_elements[0].text)

                        # Taxes
                        line_elements = element.xpath('.//ram:SpecifiedLineTradeSettlement/ram:ApplicableTradeTax/ram:RateApplicablePercent', namespaces=tree.nsmap)
                        
                        invoice_line_form.tax_ids.clear()
                        for tax_element in line_elements:
                            percentage = float(tax_element.text)

                            tax = self.env['account.tax'].search([
                                ('company_id', '=', invoice_form.company_id.id),
                                ('amount_type', '=', 'percent'),
                                ('type_tax_use', '=', invoice_form.journal_id.type),
                                ('amount', '=', percentage),
                            ], limit=1)

                            if tax:
                                invoice_line_form.tax_ids.add(tax)
                        
                        ###################################################
                        ##################Ingetive#########################
                        ###################################################
                        #Añadimos cuenta analítica por defecto del partner#
                        invoice_line_form.analytic_account_id = invoice_line_form.partner_id.cuenta_analitica_defecto_id
                        
                        
            elif amount_total_import:
                # No lines in BASICWL.
                with invoice_form.invoice_line_ids.new() as invoice_line_form:
                    invoice_line_form.name = invoice_form.comment or '/'
                    invoice_line_form.quantity = 1
                    invoice_line_form.price_unit = amount_total_import

        return invoice_form.save()

    @api.depends("amount_untaxed_signed", "invoice_date")
    def _compute_importe_validacion_euros(self):
        for r in self:
            rate = 0
            if r.invoice_date:
                euro = self.env['res.currency.rate'].search([
                    ('company_id', '=', r.company_id.id),
                    ('currency_id', '=', 1),
                    ('name', '<=', r.invoice_date.strftime('%Y-%m-%d'))
                ], limit = 1)
                if euro:
                    rate = euro.rate
            importe_original = r.amount_untaxed_signed
            r.update({'importe_validacion_euros': importe_original * rate})
            # Si no tasa para Euro el importe_validacion_euros sera igual a 0

    @api.onchange('ref')
    def _onchange_ref_invoice(self):
        for r in self:
            if r.journal_id.type == 'purchase':
                r.invoice_payment_ref = r.ref 
                
    def _compute_fecha_vencimiento_anticipo(self):
        for r in self:
            fecha_vencimiento_anticipo = None
            if r.asiento_anticipo_id:
                for line in r.asiento_anticipo_id.line_ids:
                    if line.date_maturity and line.account_id and line.account_id.group_id and \
                        line.account_id.group_id.code_prefix == '5200':
                        fecha_vencimiento_anticipo = line.date_maturity
                        break
            r.fecha_vencimiento_anticipo = fecha_vencimiento_anticipo

    @api.onchange('invoice_date')
    def _onchange_fecha_servicio(self):
        for r in self:
            if r.type == 'out_invoice' and r.invoice_date:
                fecha_servicio_primer_dia_mes = r.invoice_date.replace(day=1)
                fecha_servicio_ultimo_dia_mes_anterior = fecha_servicio_primer_dia_mes - timedelta(days=1)
                r.fecha_servicio = fecha_servicio_ultimo_dia_mes_anterior

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)

        if res.journal_id.type == 'sale':
            secuencia, name = res.generar_secuencia()
            res.write({
                'secuencia_num': secuencia,
                'secuencia': name
            })
        if 'asiento_anticipo_id' in vals:
            res.actualizar_fecha_vencimiento_asiento_anticipo()
        return res
    
    def write(self, vals):
        res = super(AccountMove, self).write(vals)
            
        if 'asiento_anticipo_id' in vals:
            self.actualizar_fecha_vencimiento_asiento_anticipo()
  
        return res

    def actualizar_fecha_vencimiento_asiento_anticipo(self):
        for r in self:
            if r.asiento_anticipo_id and r.invoice_date_due:
                r.asiento_anticipo_id.line_ids.filtered(lambda x: not x.date_maturity).write({'date_maturity': r.invoice_date_due})
    
    def generar_secuencia(self):
        self.ensure_one()
        secuencia_num = 1
        move = self.search([
            ('journal_id.type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
            ('secuencia_num', '!=', False)
        ], limit=1, order="secuencia_num desc")

        if move:
            secuencia_num = move.secuencia_num + 1

        numero_faltantes = 4 - len(str(secuencia_num))
        numero_completo = str(secuencia_num)
        for n in range(numero_faltantes):
            numero_completo = "0%s" % numero_completo

        name = "PROF/%s/%s" % (datetime.now().year, numero_completo)
        return secuencia_num, name

    @api.model
    def _get_under_validation_exceptions(self):
        res = super(AccountMove, self)._get_under_validation_exceptions()
        res += ["l10n_ar_afip_responsibility_type_id", "l10n_ar_currency_rate", 
                "invoice_date", "date", "line_ids", "invoice_payment_ref", "invoice_date_due",
                "fecha_servicio", "invoice_payment_term_id", "ref", 'payment_mode_id',
                "partner_id", "fiscal_position_id", "partner_shipping_id", "access_token","tipo_proyecto_id",
                "l10n_latam_document_number", "name", "message_main_attachment_id", 
                "invoice_paymnet_terms_id", "invoice_payment_bank_id"]
        return res
    
    @api.model
    def importar_gastos_tickelia(self):
        cnx = ConexionMysql()
        query = "SELECT * FROM Tickelia_2 where TraspasoOdoo = 0 and Cuenta_Contable != ''"
        data = cnx.execute(query)

        gastos_agrupados = {}
        for r in data:
            key = "%s-%s" % (r[u'id_Liquidaci\xf3n'], r['Tique_Factura'])
            if key not in gastos_agrupados:
                gastos_agrupados.update({key: []})
            gastos_agrupados[key].append(r)

        for key, gastos in gastos_agrupados.items():
            if not gastos:
                continue

            ref = "Liquidación %s" % gastos[0][u'id_Liquidaci\xf3n']
            date = None
            if gastos[0][u'Fecha_Liquidaci\xf3n']:
                fecha_aux = gastos[0][u'Fecha_Liquidaci\xf3n'].split(" ")[0]
                date = datetime.strptime(fecha_aux, "%d/%m/%Y").strftime("%Y-%m-%d")

            journal_id = False
            if self.env.company.tetrace_tickelia_journal_id:
                journal_id = self.env.company.tetrace_tickelia_journal_id.id

            company = self.env['res.company'].search([('vat', '=', "ES%s" % gastos[0]['NIF_Empresa'])], limit=1)

            values = {
                'ref': ref,
                'date': date,
                'journal_id': journal_id,
                'company_id': company.id if company else None,
            }

            gastos_ids = []
            line_ids = []
            for gasto in gastos:
                name = "%s%s" % (gasto['Tipo Gasto'], gasto['SubTipo_Gasto'])

                account_1 = self.env['account.account'].search([
                    ('code', '=', gasto['Cuenta_Contable']),
                    ('company_id', '=', company.id)
                ], limit=1)

                if not account_1:
                    raise ValidationError(gasto['Cuenta_Contable'])

                employee = self.env['hr.employee'].sudo().search([('identification_id', '=', gasto['DNI_Usuario'])],
                                                                 limit=1)
                partner_id = employee.address_home_id.id if employee and employee.address_home_id else None

                analytic_buscar = "46%s" % gasto['id_Proyecto']
                analytic = self.env['account.analytic.account'].search([('code', '=like', analytic_buscar)], limit=1)
                if not analytic:
                    analytic = self.env['account.analytic.account'].create({
                        'name': analytic_buscar,
                        'code': analytic_buscar
                    })

                currency = self.env['res.currency'].search([('name', '=', gasto['Moneda_Base'])], limit=1)

                cuenta_a_buscar = gasto['Cuenta_Contable_Tarjeta']
                if not cuenta_a_buscar:
                    cuenta_a_buscar = gasto['Cuenta_Contable_Anticipos']

                account_2 = self.env['account.account'].search([
                    ('code', '=', cuenta_a_buscar),
                    ('company_id', '=', company.id)
                ], limit=1)

                if not account_2:
                    continue
                #                     raise ValidationError(cuenta_a_buscar)

                debit = gasto['Importe_Base_Validado'].replace(",", ".")
                credit = gasto['Importe_Base_Validado'].replace(",", ".")

                line_ids.append((0, 0, {
                    'name': name,
                    'account_id': account_1.id if account_1 else None,
                    'partner_id': partner_id,
                    'analytic_account_id': analytic.id if analytic else None,
                    #                     'currency_id': currency.id if currency else None,
                    'debit': debit,
                    'credit': 0
                }))

                line_ids.append((0, 0, {
                    'name': name,
                    'account_id': account_2.id if account_2 else None,
                    'partner_id': partner_id,
                    #'analytic_account_id': analytic.id if analytic else None,
                    #                     'currency_id': currency.id if currency else None,
                    'debit': 0,
                    'credit': credit
                }))

                gastos_ids.append(gasto['id'])

            values.update({'line_ids': line_ids})
            self.create(values)

            
class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"
    
    @api.model
    def create_exchange_rate_entry(self, aml_to_fix, move):
        # Añadir al asiento de diferencia de cambio generado automaticamente
        # la cuenta analitica establecida en los parametros de la compañía
        res = super(AccountPartialReconcile, self).create_exchange_rate_entry(aml_to_fix, move)  
        for apunte in move.line_ids:
            # Si el tipo de cuenta del apunte es:
            # 13: Ingreso
            # 15: Gastos
            # Indicamos la cuenta analitica establecida en la compañía para estos casos
            if apunte.account_id.user_type_id.id == 13 or apunte.account_id.user_type_id.id ==15:
                apunte.write({'analytic_account_id' : apunte.company_id.tetrace_cuenta_analitica_diferencia_cambio.id})
        return res