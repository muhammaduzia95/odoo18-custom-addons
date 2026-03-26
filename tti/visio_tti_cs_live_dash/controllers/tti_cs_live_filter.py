# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_cs_live_dash\controllers\tti_cs_live_filter.py
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import date as _date  # use _date consistently


class TTICSLiveDashboardController(http.Controller):

    def _get_active_company(self):
        # Web client cookie: "cids" like "3,1" (current company first)
        cids = (request.httprequest.cookies.get("cids") or "").strip()
        cid = int(cids.split(",")[0]) if cids else request.env.user.company_id.id

        # security fallback: ensure user can access this company
        if cid not in request.env.user.company_ids.ids:
            cid = request.env.user.company_id.id

        company = request.env["res.company"].browse(cid)
        print(f"[CS-LIVE][CTX] cids={cids} active_cid={cid} env_company={request.env.company.id} allowed={request.env.context.get('allowed_company_ids')}")
        return cid, company

    def _dash_env(self):
        cid, company = self._get_active_company()
        return request.env["tti.cs.live.dashboard"].sudo().with_context(
            allowed_company_ids=[cid],
            company_id=cid,
        ).with_company(company)

    @http.route('/tti_cs_live_dashboard/filters', type='json', auth='user')
    def get_filters(self):
        """Default both dates to today."""
        today = _date.today()
        return {
            'default_date_from': today.strftime('%Y-%m-%d'),
            'default_date_to': today.strftime('%Y-%m-%d'),
        }

    @http.route('/tti_cs_live_dashboard/report_delivery', type='json', auth='user')
    def get_report_delivery(self, date_from=None, date_to=None):
        """3-slice donut: delivered(on time), late, pending."""
        today = _date.today()
        date_from = date_from or today.strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')

        print(f"[CS-LIVE] /report_delivery payload date_from={date_from}, date_to={date_to}")
        # model = request.env['tti.cs.live.dashboard'].sudo()
        # result = model.get_report_delivery_status(date_from, date_to)

        model = self._dash_env()
        result = model.get_report_delivery_status(date_from, date_to)

        print(f"[CS-LIVE] /report_delivery result={result}")
        return result

    @http.route('/tti_cs_live_dashboard/reports_due_today', type='json', auth='user')
    def get_reports_due_today(self):
        """
        Return table rows for 'Reports Due Today' (unsent SOs whose commitment_date
        falls on *today* in the user's timezone). Includes 'due_in' text.
        """
        print("[CS-LIVE] /reports_due_today called")
        # rows = request.env['tti.cs.live.dashboard'].sudo().get_reports_due_today()
        rows = self._dash_env().get_reports_due_today()

        print(f"[CS-LIVE] /reports_due_today rows={len(rows)}")
        return {'rows': rows}

    @http.route('/tti_cs_live_dashboard/right_person_summary', type='json', auth='user')
    def right_person_summary(self, date_from=None, date_to=None):
        """Right table: respects date range (filters)."""
        today = _date.today()
        date_from = date_from or today.strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')
        print(f"[CS-LIVE] /right_person_summary payload date_from={date_from}, date_to={date_to}")
        # rows = request.env['tti.cs.live.dashboard'].sudo().get_right_person_summary(date_from, date_to)

        rows = self._dash_env().get_right_person_summary(date_from, date_to)

        print(f"[CS-LIVE] /right_person_summary rows={len(rows)}")
        return {'rows': rows}
