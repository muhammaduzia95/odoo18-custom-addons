# -*- coding: utf-8 -*-
{
    'name': "Quran Academy Payroll Customization",
    'summary': "Customization of Hr Payroll",
    'description': """Customization of HR Payroll""",

    'author': "Visiomate",
    'website': "https://www.visiomate.com",

    'depends': ['base', 'hr', 'hr_skills', 'om_hr_payroll', 'hr_holidays' , 'web'],
    'category': 'Uncategorized',
    'license': 'LGPL-3',
    'version': '18.0.1.0.4',
    'sequence': -110,

    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'data/employee_sequence.xml',
        'data/department_sequence.xml',
        'data/paper_format.xml',
        'wizard/duplicate_payslips.xml',
        'wizard/post_payslips.xml',
        'wizard/import_exel_wizard.xml',
        'wizard/pdf_reports.xml',
        'wizard/email_payslips_wizard.xml',
        # 'wizard/warning_confirm.xml',

        'report/header_footer.xml',
        'report/report_action.xml',
        'report/yearly_salary_worker.xml',
        'report/pay_receiving_list.xml',
        'report/salary_summary.xml',
        'report/pay_receiving_bank_sheet.xml',
        'report/pay_receiving_cash_sheet.xml',
        'report/pay_receiving_cash_list.xml',
        'report/payroll_sheet.xml',
        'report/hr_employee_badge.xml',
        'report/payslip.xml',
        'report/eobi_anjuman_report.xml',
        'report/eobi_maktaba_report.xml',

        'views/hr_employee.xml',
        'views/payslip_dashboard_action.xml',
        'views/hr_department.xml',
        'views/eobi_page.xml',
        'views/hr_payslip.xml',
        'views/hr_contract.xml',
        'views/employee_medical.xml',
        'views/paid_by_summary.xml',
        'views/paid_by_summary_category.xml',
        'views/over_time_this_month.xml',
        'views/loan_this_month.xml',
        'views/medical_this_month.xml',
        'views/wpay_this_month.xml',
        'views/eobi_this_month.xml',
        'views/eobi_arrear_this_month.xml',
        'views/salary_statement_this_month.xml',
        'views/pay_receiving_cash.xml',
        'views/pay_receiving_bank.xml',
        'views/current_month.xml',
        'views/salary_summary.xml',

        'report/views/payReceivingBankList_view.xml',
        'report/views/payReceivingCashList_view.xml',
        'report/views/salarySummary_view.xml',
        'report/views/payReceivingBankSheet_view.xml',
        'report/views/payReceivingCashSheet_view.xml',
        'report/views/payrollSheet_view.xml',
        'report/yearly_gross_salary_statement_worker.xml',

        'report/views/menus.xml',
        'wizard/yearly_salary_worker.xml',

    ],

    'assets': {
        'web.assets_backend': [
            # 'visio_payroll_customization/static/src/js/export.js',
            'visio_payroll_customization/static/src/views/*.js',
            'visio_payroll_customization/static/src/views/*.xml',
        ],
    },

    'demo': [],
    'application': True,
    'installable': True,

}
