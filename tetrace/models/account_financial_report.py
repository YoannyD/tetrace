# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import ast

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, ustr
from odoo.tools.safe_eval import safe_eval
from odoo.addons.account_reports.models.account_financial_report import FormulaContext, FormulaLine

_logger = logging.getLogger(__name__)


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    informe_fecha_contable = fields.Boolean('Informe con fecha contable')


class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    def _query_get_select_sum(self, currency_table):
        """ Little function to help building the SELECT statement when computing the report lines.

            @param currency_table: dictionary containing the foreign currencies (key) and their factor (value)
                compared to the current user's company currency
            @returns: the string and parameters to use for the SELECT
        """
        decimal_places = self.env.company.currency_id.decimal_places
        used_currency = self.env.company.currency_id.with_context(company_id=self.env.company.id)
        extra_params = []
        select = '''
            COALESCE(SUM(\"account_move_line\".balance), 0) AS balance,
            COALESCE(SUM(\"account_move_line\".amount_residual), 0) AS amount_residual,
            COALESCE(SUM(\"account_move_line\".debit), 0) AS debit,
            COALESCE(SUM(\"account_move_line\".credit), 0) AS credit
        '''
        if currency_table:
            financial_report_aux = self._get_financial_report()
            if financial_report_aux and financial_report_aux.informe_fecha_contable:
                select = '''
                    COALESCE(SUM(ROUND(\"account_move_line\".balance * (%s / \"cr\".rate), %s)), 0) AS balance,
                    COALESCE(SUM(ROUND(\"account_move_line\".amount_residual * (%s / \"cr\".rate), %s)), 0) AS amount_residual,
                    COALESCE(SUM(ROUND(\"account_move_line\".debit * (%s / \"cr\".rate), %s)), 0) AS debit,
                    COALESCE(SUM(ROUND(\"account_move_line\".credit * (%s / \"cr\".rate), %s)), 0) AS credit
                '''
                extra_params += [used_currency.rate, decimal_places,
                                 used_currency.rate, decimal_places,
                                 used_currency.rate, decimal_places,
                                 used_currency.rate, decimal_places]
            else:
                select = 'COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"account_move_line\".company_currency_id = %s THEN ROUND(\"account_move_line\".balance * %s, %s) '
                select += 'ELSE \"account_move_line\".balance END), 0) AS balance, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"account_move_line\".company_currency_id = %s THEN ROUND(\"account_move_line\".amount_residual * %s, %s) '
                select += 'ELSE \"account_move_line\".amount_residual END), 0) AS amount_residual, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"account_move_line\".company_currency_id = %s THEN ROUND(\"account_move_line\".debit * %s, %s) '
                select += 'ELSE \"account_move_line\".debit END), 0) AS debit, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"account_move_line\".company_currency_id = %s THEN ROUND(\"account_move_line\".credit * %s, %s) '
                select += 'ELSE \"account_move_line\".credit END), 0) AS credit'

        return select, extra_params

    def _compute_line(self, currency_table, financial_report, group_by=None, domain=[]):
        """ Computes the sum that appeas on report lines when they aren't unfolded. It is using _query_get() function
            of account.move.line which is based on the context, and an additional domain (the field domain on the report
            line) to build the query that will be used.

            @param currency_table: dictionary containing the foreign currencies (key) and their factor (value)
                compared to the current user's company currency
            @param financial_report: browse_record of the financial report we are willing to compute the lines for
            @param group_by: used in case of conditionnal sums on the report line
            @param domain: domain on the report line to consider in the query_get() call

            @returns : a dictionnary that has for each aml in the domain a dictionnary of the values of the fields
        """
        domain = domain and ast.literal_eval(ustr(domain))
        for index, condition in enumerate(domain):
            if condition[0].startswith('tax_ids.'):
                new_condition = (condition[0].partition('.')[2], condition[1], condition[2])
                taxes = self.env['account.tax'].with_context(active_test=False).search([new_condition])
                domain[index] = ('tax_ids', 'in', taxes.ids)
        aml_obj = self.env['account.move.line']
        tables, where_clause, where_params = aml_obj._query_get(domain=self._get_aml_domain())

        financial_report_aux = self._get_financial_report()
        if financial_report_aux and financial_report_aux.informe_fecha_contable:
            tables += """,(
                SELECT
                    ml.id,
                    COALESCE(cr.rate, 1.0) AS rate
                FROM
                    res_currency_rate cr INNER JOIN
                    account_move_line ml
                    ON cr.currency_id = ml.company_currency_id and cr.name = ml.date
                WHERE
                    cr.company_id = %s
                ORDER BY cr.name DESC
                ) AS cr
                """ % self.env.company.id
            where_clause = "(\"cr\".\"id\" = \"account_move_line\".\"id\") AND " + where_clause

        if financial_report.tax_report:
            where_clause += ''' AND "account_move_line".tax_exigible = 't' '''

        select, select_params = self._query_get_select_sum(currency_table)
        where_params = select_params + where_params

        if (self.env.context.get('sum_if_pos') or self.env.context.get('sum_if_neg')) and group_by:
            sql = "SELECT account_move_line." + group_by + " as " + group_by + "," + select + " FROM " + tables + " WHERE " + where_clause + " GROUP BY account_move_line." + group_by
            self.env.cr.execute(sql, where_params)
            res = {'balance': 0, 'debit': 0, 'credit': 0, 'amount_residual': 0}
            for row in self.env.cr.dictfetchall():
                if (row['balance'] > 0 and self.env.context.get('sum_if_pos')) or (
                    row['balance'] < 0 and self.env.context.get('sum_if_neg')):
                    for field in ['debit', 'credit', 'balance', 'amount_residual']:
                        res[field] += row[field]
            res['currency_id'] = self.env.company.currency_id.id
            return res

        sql, params = self._build_query_compute_line(select, tables, where_clause, where_params)
        self.env.cr.execute(sql, params)
        results = self.env.cr.dictfetchall()[0]
        results['currency_id'] = self.env.company.currency_id.id
        return results

    def _eval_formula(self, financial_report, debit_credit, currency_table, linesDict_per_group, groups=False):
        groups = groups or {'fields': [], 'ids': [()]}
        debit_credit = debit_credit and financial_report.debit_credit
        formulas = self._split_formulas()
        currency = self.env.company.currency_id

        line_res_per_group = []

        if not groups['ids']:
            return [{'line': {'balance': 0.0}}]

        # this computes the results of the line itself
        for group_index, group in enumerate(groups['ids']):
            self_for_group = self.with_context(group_domain=self._get_group_domain(group, groups))
            linesDict = linesDict_per_group[group_index]
            line = False

            if self.code and self.code in linesDict:
                line = linesDict[self.code]
            elif formulas and formulas['balance'].strip() == 'count_rows' and self.groupby:
                line_res_per_group.append({'line': {'balance': self_for_group._get_rows_count()}})
            elif formulas and formulas['balance'].strip() == 'from_context':
                line_res_per_group.append({'line': {'balance': self_for_group._get_value_from_context()}})
            else:
                line = FormulaLine(self_for_group, currency_table, financial_report, linesDict=linesDict)

            if line:
                res = {}
                res['balance'] = line.balance
                res['balance'] = currency.round(line.balance)
                if debit_credit:
                    res['credit'] = currency.round(line.credit)
                    res['debit'] = currency.round(line.debit)
                line_res_per_group.append(res)

        # don't need any groupby lines for count_rows and from_context formulas
        if all('line' in val for val in line_res_per_group):
            return line_res_per_group

        columns = []
        # this computes children lines in case the groupby field is set
        if self.domain and self.groupby and self.show_domain != 'never':
            if self.groupby not in self.env['account.move.line']:
                raise ValueError(_('Groupby should be a field from account.move.line'))

            groupby = [self.groupby or 'id']
            if groups:
                groupby = groups['fields'] + groupby
            groupby = ', '.join(['"account_move_line".%s' % field for field in groupby])

            aml_obj = self.env['account.move.line']
            tables, where_clause, where_params = aml_obj._query_get(domain=self._get_aml_domain())

            financial_report_aux = self._get_financial_report()
            if financial_report_aux.informe_fecha_contable:
                tables += """,(
                    SELECT
                        ml.id,
                        COALESCE(cr.rate, 1.0) AS rate
                    FROM
                        res_currency_rate cr INNER JOIN
                        account_move_line ml
                        ON cr.currency_id = ml.company_currency_id and cr.name = ml.date
                    WHERE
                        cr.company_id = %s
                    ORDER BY cr.name DESC
                    ) AS cr
                    """ % self.env.company.id
                where_clause = "(\"cr\".\"id\" = \"account_move_line\".\"id\") AND " + where_clause

            if financial_report.tax_report:
                where_clause += ''' AND "account_move_line".tax_exigible = 't' '''

            select, params = self._query_get_select_sum(currency_table)
            params += where_params

            sql, params = self._build_query_eval_formula(groupby, select, tables, where_clause, params)
            self.env.cr.execute(sql, params)
            results = self.env.cr.fetchall()
            for group_index, group in enumerate(groups['ids']):
                linesDict = linesDict_per_group[group_index]
                results_for_group = [result for result in results if group == result[:len(group)]]
                if results_for_group:
                    results_for_group = [r[len(group):] for r in results_for_group]
                    results_for_group = dict(
                        [(k[0], {'balance': k[1], 'amount_residual': k[2], 'debit': k[3], 'credit': k[4]}) for k in
                         results_for_group])
                    c = FormulaContext(self.env['account.financial.html.report.line'].with_context(
                        group_domain=self._get_group_domain(group, groups)),
                                       linesDict, currency_table, financial_report, only_sum=True)
                    if formulas:
                        for key in results_for_group:
                            c['sum'] = FormulaLine(results_for_group[key], currency_table, financial_report,
                                                   type='not_computed')
                            c['sum_if_pos'] = FormulaLine(
                                results_for_group[key]['balance'] >= 0.0 and results_for_group[key] or {'balance': 0.0},
                                currency_table, financial_report, type='not_computed')
                            c['sum_if_neg'] = FormulaLine(
                                results_for_group[key]['balance'] <= 0.0 and results_for_group[key] or {'balance': 0.0},
                                currency_table, financial_report, type='not_computed')
                            for col, formula in formulas.items():
                                if col in results_for_group[key]:
                                    results_for_group[key][col] = safe_eval(formula, c, nocopy=True)
                    to_del = []
                    for key in results_for_group:
                        if self.env.company.currency_id.is_zero(results_for_group[key]['balance']):
                            to_del.append(key)
                    for key in to_del:
                        del results_for_group[key]
                    results_for_group.update({'line': line_res_per_group[group_index]})
                    columns.append(results_for_group)
                else:
                    res_vals = {'balance': 0.0}
                    if debit_credit:
                        res_vals.update({'debit': 0.0, 'credit': 0.0})
                    columns.append({'line': res_vals})

        return columns or [{'line': res} for res in line_res_per_group]


