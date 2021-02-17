# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import _, fields
from datetime import datetime
from collections import defaultdict
from odoo.addons.mis_builder.models.aep import AccountingExpressionProcessor
from odoo.addons.mis_builder.models.accounting_none import AccountingNone
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountingExpressionProcessor(AccountingExpressionProcessor):
    def __init__(self, companies, currency=None, account_model="account.account", informe_fecha_contable=False):
        self.env = companies.env
        self.companies = companies
        if not currency:
            self.currency = companies.mapped("currency_id")
            if len(self.currency) > 1:
                raise UserError(
                    _(
                        "If currency_id is not provided, "
                        "all companies must have the same currency."
                    )
                )
        else:
            self.currency = currency
        self.dp = self.currency.decimal_places
        # before done_parsing: {(ml_domain, mode): set(acc_domain)}
        # after done_parsing: {(ml_domain, mode): list(account_ids)}
        self._map_account_ids = defaultdict(set)
        # {account_domain: set(account_ids)}
        self._account_ids_by_acc_domain = defaultdict(set)
        # smart ending balance (returns AccountingNone if there
        # are no moves in period and 0 initial balance), implies
        # a first query to get the initial balance and another
        # to get the variation, so it's a bit slower
        self.smart_end = True
        # Account model
        self._account_model = self.env[account_model].with_context(active_test=False)
        self._informe_fecha_contable = informe_fecha_contable

    def _get_company_rates(self, date):
        # get exchange rates for each company with its rouding
        company_rates = {}
        # target_rate = self.currency.with_context(date=date).rate

        for company in self.companies:
            if company.currency_id != self.currency:
                cr = self.currency._get_rates(company, date)
                rate = 1.0
                for key, value in cr.items():
                    rate = value
                    break
            else:
                rate = 1.0
            company_rates[company.id] = (rate, company.currency_id.decimal_places)
        return company_rates

    def do_queries(
        self,
        date_from,
        date_to,
        target_move="posted",
        additional_move_line_filter=None,
        aml_model=None,
    ):
        """Query sums of debit and credit for all accounts and domains
        used in expressions.

        This method must be executed after done_parsing().
        """
        if not aml_model:
            aml_model = self.env["account.move.line"]
        else:
            aml_model = self.env[aml_model]
        aml_model = aml_model.with_context(active_test=False)
        # company_rates = self._get_company_rates(date_to)
        # {(domain, mode): {account_id: (debit, credit)}}
        self._data = defaultdict(dict)
        domain_by_mode = {}
        ends = []
        for key in self._map_account_ids:
            domain, mode = key
            if mode == self.MODE_END and self.smart_end:
                # postpone computation of ending balance
                ends.append((domain, mode))
                continue
            if mode not in domain_by_mode:
                domain_by_mode[mode] = self.get_aml_domain_for_dates(
                    date_from, date_to, mode, target_move
                )
                
            domain = list(domain) + domain_by_mode[mode]
            domain.append(("account_id", "in", self._map_account_ids[key]))
            if additional_move_line_filter:
                domain.extend(additional_move_line_filter)
            # fetch sum of debit/credit, grouped by account_id
            
            accs = aml_model.with_context(lang="en_US").read_group(
                domain,
                ["debit", "credit", "account_id", "company_id", "date"],
                ["account_id", "company_id", "date:day"],
                lazy=False,
            )
            
            for acc in accs:
                fecha_rate = datetime.strptime(acc["date:day"], "%d %b %Y")
                fecha_rate = fecha_rate if self._informe_fecha_contable else date_to
                company_rates = self._get_company_rates(fecha_rate)
                rate, dp = company_rates[acc["company_id"][0]]
                debit = acc["debit"] or 0.0
                credit = acc["credit"] or 0.0
                if mode in (self.MODE_INITIAL, self.MODE_UNALLOCATED) and float_is_zero(
                    debit - credit, precision_digits=self.dp
                ):
                    # in initial mode, ignore accounts with 0 balance
                    continue

                if acc["account_id"][0] not in self._data[key]:
                    self._data[key].update({acc["account_id"][0]: (0, 0)})

                valores = list(self._data[key][acc["account_id"][0]])
                d = valores[0] + debit * rate
                c = valores[1] + credit * rate
                self._data[key][acc["account_id"][0]] = (d, c)
        # compute ending balances by summing initial and variation
        for key in ends:
            domain, mode = key
            initial_data = self._data[(domain, self.MODE_INITIAL)]
            variation_data = self._data[(domain, self.MODE_VARIATION)]
            account_ids = set(initial_data.keys()) | set(variation_data.keys())
            for account_id in account_ids:
                di, ci = initial_data.get(account_id, (AccountingNone, AccountingNone))
                dv, cv = variation_data.get(
                    account_id, (AccountingNone, AccountingNone)
                )
                self._data[key][account_id] = (di + dv, ci + cv)
