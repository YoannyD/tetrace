# Copyright 2020 ForgeFlow
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade  # pylint: disable=W7936

field_renames = [
    (
        "l10n.es.aeat.mod349.report",
        "l10n.es.aeat.mod349.report",
        "type",
        "statement_type",
    ),
    (
        "account.tax.template",
        "account.tax.template",
        "aeat_349_operation_key",
        "aeat_349_map_line",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, field_renames)
