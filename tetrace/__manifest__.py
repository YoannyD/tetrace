# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>
{
    'name': "Tetrace",
    'summary': """""",
    'description': """""",
    'author': "Ingetive",
    'website': "https://ingetive.com",
    'category': 'Uncategorized',
    'version': '13.0.1.0.1',
    'depends': [
        'base',
        'sale',
        'purchase',
        'account',
        'account_reports',
        'account_intrastat',
        'l10n_ar',
        'l10n_cl',
        'l10n_latam_invoice_document',
        'account_due_list',
        'hr',
        'hr_recruitment',
        'hr_timesheet',
        'sale_timesheet',
        'account_move_tier_validation',
        'documents',
        'documents_hr',
        'project',
        'analytic',
        'mis_builder',
        'account_asset',
        'base_tier_validation',
        'report_xlsx',
        'account_analytic_required',
        'account_facturx',
        'l10n_es_vat_book',
        'l10n_es_aeat_mod303',
        'sale_timesheet_enterprise'
    ],
    'data': [
        'security/tetrace_security.xml',
        'security/ir.model.access.csv',
        'data/project.xml',
        'data/mail_activity.xml',
        'data/mail_sale_order.xml',
        'data/mail_tetrace_viaje.xml',
        'report/sale.xml',
        'report/account.xml',
        'report/web.xml',
        'report/tetrace_its.xml',
        'report/mis_report_instance_xlsx_multi_tab.xml',
        'report/purchase.xml',
        'report/l10n_ar.xml',
        'views/web.xml',
        'views/account_financial_report.xml',
        'views/account_move_line.xml',
        'views/account_account.xml',
        'views/account_move.xml',
        'views/hr_applicant.xml',
        'views/hr_employee.xml',
        'views/product_category.xml',
        'views/product_template.xml',
        'views/tetrace_skills.xml',
        'views/tetrace_nomina.xml',
        'views/tetrace_tipo_contrato.xml',
        'views/tetrace_validacion.xml',
        'views/tetrace_sale_order_version.xml',
        'views/tetrace_tipo_proyecto.xml',
        'views/tetrace_tipo_servicio.xml',
        'views/hr_contract.xml',
        'views/res_company.xml',
        'views/res_users.xml',
        'views/project.xml',
        'views/documents.xml',
        'views/purchase.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
        'views/stock_move.xml',
        'views/mis_report_instance.xml',
        'views/tetrace_tickelia.xml',
        'views/tetrace_vat_book.xml',
        'views/account_analytic_account.xml',
        'views/res_config_settings.xml',
        'views/tetrace_linea_analitica_rel.xml',
        'views/tetrace_gestion_facturacion.xml',
        'wizard/asset_modify.xml',
        'wizard/tetrace_importar_nomina.xml',
        'wizard/tetrace_crear_version.xml',
        'wizard/tetrace_importar_tickelia.xml',
        'wizard/tetrace_generar_prevision_facturacion.xml',
        'wizard/tetrace_merge_analytic_account.xml',
        'wizard/tetrace_activar_tarea.xml',
        'wizard/tetrace_importar_producto_pv.xml',
        'wizard/tetrace_prevision_facturacion_cancelar.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
