import json
import base64
from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta
from odoo.fields import Datetime


class SaleOrderStatusAPI(http.Controller):

    @http.route('/api/lims_sale_order_status', type='json', auth='public', methods=['POST'])
    def manage_sale_order_status(self, **kwargs):
        try:
            sale_order_id = kwargs.get('sale_order_id')
            tti_lims_test_id = kwargs.get('lims_test_id')
            product_name = kwargs.get('test_name')
            status = kwargs.get('status')

            if not tti_lims_test_id:
                return {"status": "error", "message": "'lims_test_id' not given!!!"}
            if not sale_order_id:
                return {"status": "error", "message": "'sale_order_id' not given!!!"}
            # if not product_name:
            #     return {"status": "error", "message": "'test_name' not given!!!"}
            if not status:
                return {"status": "error", "message": "'status' not given!!!"}

            tti_lims_test_id = request.env['product.template'].sudo().search(
                [
                    ("default_code", "=", tti_lims_test_id),
                    ("test_type", "=", "test_report")
                ], limit=1
            )
            if not tti_lims_test_id:
                return {"status": "error", "message": f"LIMS Test not found in Odoo with '{tti_lims_test_id}'"}

            sale_order = request.env['sale.order'].sudo().search(
                [('name', '=', sale_order_id)], limit=1
            )
            if not sale_order:
                return {"status": "error", "message": f"Odoo Sale Order not found with '{sale_order_id}'"}

            log_entry = request.env['tti.so.lims.tests.status.logs'].sudo().search([
                ('sale_order_id', '=', sale_order_id),
                ('tti_lims_test_id', '=', tti_lims_test_id.id),
            ], limit=1)

            if log_entry:
                log_entry.sudo().write(
                    {
                        'status': status,
                    }
                )
                return {"status": "success", "message": "Log updated successfully", "log_id": log_entry.id}
            else:
                new_log_entry = request.env['tti.so.lims.tests.status.logs'].sudo().create({
                    'name': f'LIMS Test Status Log for Sale Order: {sale_order_id}',
                    'sale_order_id': sale_order.id if sale_order else False,
                    'order_id': sale_order.id  if sale_order else sale_order_id,
                    'product_name': tti_lims_test_id.name,
                    'tti_lims_test_id': tti_lims_test_id.id,
                    'status': status,
                })
                return {"status": "success", "message": "Log created successfully", "log_id": new_log_entry.id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @http.route('/api/lims_create_test_product', type='json', auth='public', methods=['POST'])
    def lims_create_test_product(self, **kwargs):
        try:
            tti_lims_test_id = kwargs.get('lims_test_id')
            name = kwargs.get('test_name')
            tti_test_method = kwargs.get('test_method_name')
            default_code = kwargs.get('test_code')
            list_price = kwargs.get('test_rate')
            tti_department_id = kwargs.get('test_department', False)
            tti_test_group_id = kwargs.get('test_group', False)
            test_type = 'test_report'
            type = 'service'

            if not tti_lims_test_id:
                return {"status": "error", "message": "No LIMS Test ID specified"}
            if not name:
                return {"status": "error", "message": "No Test Name specified"}
            if not default_code:
                return {"status": "error", "message": "No Test Code specified"}

            product_exist = request.env['product.template'].sudo().search([
                # ('name', '=', name),
                # ('tti_test_method', '=', tti_test_method),
                ('test_type', '=', test_type),
                ('default_code', '=', default_code),
                # ('tti_lims_test_id', '=', tti_lims_test_id),
                ('type', '=', type),
            ])
            if product_exist:
                return {"status": "error", "message": f"Test '{name}' already exists with test code '{default_code}' of method '{tti_test_method}'"}


            tti_department_id = request.env['tti.si.department'].sudo().search([
                '|',
                ('code', '=', tti_department_id),
                ('name', '=', tti_department_id),
            ], limit=1)
            if not tti_department_id:
                tti_department_id = request.env['tti.si.department'].sudo().create({
                    'name': tti_department_id
                })
            # tti_test_group_id = request.env['tti.si.test.group'].sudo().search([
            #     ('name', '=', tti_test_group_id),
            # ])
            # if not tti_test_group_id:
            #     tti_test_group_id = request.env['tti.si.test.group'].sudo().create({
            #         'name': tti_test_group_id
            #     })

            tti_test_product = request.env['product.template'].sudo().create({
                'tti_lims_test_id': tti_lims_test_id,
                'name': name,
                'tti_test_method': tti_test_method,
                'list_price_usd': list_price,
                'default_code': default_code,
                'sale_ok': True,
                'purchase_ok': False,
                'tti_department_id': tti_department_id.id if tti_department_id else False,
                # 'tti_test_group_id': tti_test_group_id.id if tti_test_group_id else False,
                'test_type': test_type,
                'type': type,
            })
            return {"status": "success", "message": f"Test '{name}' created successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


    @http.route('/api/lims_create_package_product', type='json', auth='public', methods=['POST'])
    def lims_create_package_product(self, **kwargs):
        try:
            tti_lims_package_id = kwargs.get('lims_package_id')
            name = kwargs.get('package_name')
            tti_test_method = kwargs.get('package_method_name')
            default_code = kwargs.get('package_code')
            list_price = kwargs.get('package_rate')
            tti_department_id = kwargs.get('package_department', False)
            # tti_test_group_id = kwargs.get('package_group', False)
            package_test_reports = kwargs.get('package_test_reports', [])
            test_type = 'test_package'
            type = 'service'

            if not tti_lims_package_id:
                return {"status": "error", "message": "No LIMS Package ID specified"}
            if not name:
                return {"status": "error", "message": "No Package Name specified"}
            if not default_code:
                return {"status": "error", "message": "No Package Code specified"}

            package_exist = request.env['product.template'].sudo().search([
                # ('name', '=', name),
                # ('tti_test_method', '=', tti_test_method),
                ('default_code', '=', default_code),
                ('test_type', '=', test_type),
                # ('tti_lims_package_id', '=', tti_lims_package_id),
                ('type', '=', type),
            ])
            if package_exist:
                return {"status": "error", "message": f"Package '{name}' already exists with test code '{default_code}'"}


            tti_department_id = request.env['tti.si.department'].sudo().search([
                '|',
                ('code', '=', tti_department_id),
                ('name', '=', tti_department_id),
            ], limit=1)
            # if not tti_department_id:
            #     tti_department_id = request.env['tti.si.department'].sudo().create({
            #         'name': tti_lims_test_id
            #     })
            # tti_test_group_id = request.env['tti.si.test.group'].sudo().search([
            #     ('name', '=', tti_test_group_id),
            # ])
            # if not tti_test_group_id:
            #     tti_test_group_id = request.env['tti.si.test.group'].sudo().create({
            #         'name': tti_test_group_id
            #     })


            tti_package_product = request.env['product.template'].sudo().create({
                'tti_lims_test_id': tti_lims_package_id,
                'name': name,
                'tti_test_method': tti_test_method,
                'list_price_usd': list_price,
                'default_code': default_code,
                'sale_ok': True,
                'purchase_ok': False,
                'tti_department_id': tti_department_id.id if tti_department_id else False,
                # 'tti_test_group_id': tti_test_group_id.id if tti_test_group_id else False,
                'test_type': test_type,
                'type': type,
            })

            if tti_package_product:
                test_report_list = self.create_test_report(package_test_reports, tti_package_product)
                tti_package_product.write({
                    'test_report_ids': test_report_list,
                })
            return {"status": "success", "message": f"Package '{name}' created successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def create_test_report(self, package_test_reports, tti_package_product):
        test_report_list = []
        test_type = 'test_report'
        type = 'service'

        for kwargs in package_test_reports:
            tti_lims_test_id = kwargs.get('lims_test_id')
            name = kwargs.get('test_name')
            tti_test_method = kwargs.get('test_method_name')
            default_code = kwargs.get('test_code')
            list_price = kwargs.get('test_rate')
            tti_department_id = kwargs.get('test_department', False)
            tti_test_group_id = kwargs.get('test_group', False)

            # if not tti_lims_test_id:
            #     continue
            if not name:
                continue
            if not default_code:
                continue

            product_test = request.env['product.template'].sudo().search([
                # ('name', '=', name),
                # ('tti_test_method', '=', tti_test_method),
                ('test_type', '=', test_type),
                ('default_code', '=', default_code),
                # ('tti_lims_test_id', '=', tti_lims_test_id),
                ('type', '=', type),
            ])
            if not product_test:

                tti_department_id = request.env['tti.si.department'].sudo().search([
                    '|',
                    ('code', '=', tti_department_id),
                    ('name', '=', tti_department_id),
                ], limit=1)
                # if not tti_department_id:
                #     tti_department_id = request.env['tti.si.department'].sudo().create({
                #         'name': tti_lims_test_id
                #     })
                # tti_test_group_id = request.env['tti.si.test.group'].sudo().search([
                #     ('name', '=', tti_test_group_id),
                # ])
                # if not tti_test_group_id:
                #     tti_test_group_id = request.env['tti.si.test.group'].sudo().create({
                #         'name': tti_test_group_id
                #     })

                product_test = request.env['product.template'].sudo().create({
                    'tti_lims_test_id': tti_lims_test_id,
                    'name': name,
                    'tti_test_method': tti_test_method,
                    'list_price_usd': list_price,
                    'sale_ok': True,
                    'purchase_ok': False,
                    'default_code': default_code,
                    'tti_department_id': tti_department_id.id if tti_department_id else False,
                    # 'tti_test_group_id': tti_test_group_id.id if tti_test_group_id else False,
                    'test_type': test_type,
                    'type': type,
                })


            dict_test = {
                "qty": kwargs.get("test_qty", 1),
                "product_id": tti_package_product.id,
                "test_report": product_test.id,
            }
            test_report_list.append((0, 0, dict_test))
        return test_report_list


    @http.route('/api/tti_create_calendar_meeting', type='json', auth='public', methods=['POST'])
    def tti_create_calendar_meeting(self, **kwargs):
        try:
            start = kwargs.get('start_date')
            name = kwargs.get('customer_name')
            email = kwargs.get('customer_email')


            if not start:
                return {"status": "error", "message": "No Start Date specified"}
            if not name:
                return {"status": "error", "message": "No Customer Name specified"}
            if not email:
                return {"status": "error", "message": "No Customer Email specified"}

            dt_object = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")

            partner_id = request.env['res.partner'].sudo().search([
                ('email', '=', email),
            ])
            if not partner_id:
                partner_id = request.env['res.partner'].sudo().create({
                    'name': name,
                    'email': email,
                })

            calendar_event = request.env['calendar.event'].sudo().create({
                'name': f"{name} Meeting",
                'start': dt_object,
                'stop': dt_object + timedelta(minutes=30),
                'partner_ids': partner_id.ids,
            })
            if not calendar_event:
                return {"status": "error", "message": "Failed to create meeting"}
            return {"status": "success", "message": f"Meeting created for {name}", "calendar_event": calendar_event.id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @http.route('/api/tti_create_crm_pipeline', type='json', auth='public', methods=['POST'])
    def tti_create_crm_pipeline(self, **kwargs):
        try:
            name = kwargs.get('customer_name')
            email = kwargs.get('customer_email')
            description = kwargs.get('customer_description')


            if not name:
                return {"status": "error", "message": "No Customer Name specified"}
            if not email:
                return {"status": "error", "message": "No Customer Email specified"}

            partner_id = request.env['res.partner'].sudo().search([
                ('email', '=', email),
            ], limit=1)
            if not partner_id:
                partner_id = request.env['res.partner'].sudo().create({
                    'name': name,
                    'email': email,
                })

            template_name = 'Test Email API'
            template_id = request.env['mail.template'].sudo().search([('name', '=', template_name)])
            if template_id:
                mail_values = {
                    'subject': template_id.subject or 'Email',
                    'body_html': template_id.body_html,
                    'email_from': template_id.email_from,
                    'email_to': email,
                }
                # Send the email
                mail = request.env['mail.mail'].sudo().create(mail_values)
                mail.send()

            crm_lead = request.env['crm.lead'].sudo().create({
                'name': f"{name}'s opportunity",
                'partner_id': partner_id.id,
                'email_from': email,
                'description': description,
            })
            if not crm_lead:
                return {"status": "error", "message": "Failed to create CRM lead"}
            return {"status": "success", "message": "Created CRM lead", "crm_pipeline": crm_lead.id}
        except Exception as e:
            return {"status": "error", "message": str(e)}


