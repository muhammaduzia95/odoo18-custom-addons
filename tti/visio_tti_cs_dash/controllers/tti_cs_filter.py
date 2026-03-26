# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_cs_dash\controllers\tti_cs_filter.py
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import date
from odoo import models, fields, api


class TTICSDashboardController(http.Controller):

    def _get_active_company(self):
        # Web client cookie: "cids" like "3,1" (current company first)
        cids = (request.httprequest.cookies.get("cids") or "").strip()
        cid = int(cids.split(",")[0]) if cids else request.env.user.company_id.id

        # security fallback: ensure user can access this company
        if cid not in request.env.user.company_ids.ids:
            cid = request.env.user.company_id.id

        company = request.env["res.company"].browse(cid)
        print(f"[CS DASH][CTX] cids={cids} active_cid={cid} env_company={request.env.company.id} allowed={request.env.context.get('allowed_company_ids')}")
        return cid, company

    def _dash_env(self):
        cid, company = self._get_active_company()
        return request.env["tti.cs.dashboard"].sudo().with_context(
            allowed_company_ids=[cid],
            company_id=cid,
        ).with_company(company)

    def _effective_user_id(self, incoming_user_id: int):
        """Managers may choose any; non-managers are forced to themselves."""
        user = request.env.user
        is_manager = user.has_group('visio_tti_report_sending.group_sale_order_send_report_manager')
        if is_manager:
            try:
                return int(incoming_user_id or 0)
            except Exception:
                return 0
        # Non-manager
        return user.id

    @http.route('/tti_cs_dashboard/filters', type='json', auth='user')
    def get_filters(self):
        """Return defaults + CS personnel, and who can edit it (manager only)."""
        today = date.today()
        first_day = date(today.year, today.month, 1)

        env = request.env
        user = env.user
        cid, company = self._get_active_company()

        # groups
        is_manager = user.has_group('visio_tti_report_sending.group_sale_order_send_report_manager')

        personnel = []
        default_user_id = user.id

        if is_manager:
            # Manager: "All" + everyone (sorted)
            # groups = env['sale.order'].sudo().read_group(
            #     domain=[('user_id', '!=', False)],
            #     fields=['user_id'],
            #     groupby=['user_id'],
            # )
            groups = env['sale.order'].sudo().with_context(
                allowed_company_ids=[cid],
                company_id=cid,
            ).with_company(company).read_group(
                domain=[('user_id', '!=', False), ('company_id', '=', cid)],
                fields=['user_id'],
                groupby=['user_id'],
            )

            user_ids = [g['user_id'][0] for g in groups if g.get('user_id')]
            users = env['res.users'].sudo().browse(user_ids).sorted(lambda u: (u.name or "").lower())

            personnel.append({'id': 0, 'name': 'All'})
            personnel += [{'id': u.id, 'name': u.name} for u in users]
            default_user_id = 0
        else:
            # Non-manager: only themselves; dropdown should be readonly on UI
            personnel = [{'id': user.id, 'name': user.name}]
            default_user_id = user.id

        return {
            'default_date_from': first_day.strftime('%Y-%m-%d'),
            'default_date_to': today.strftime('%Y-%m-%d'),
            'cs_personnel': personnel,
            'default_user_id': default_user_id,
            'can_edit_personnel': is_manager,  # 👈 UI uses this to disable dropdown
        }

    # ADD THIS
    @http.route('/tti_cs_dashboard/data', type='json', auth='user')
    def get_data(self, date_from=None, date_to=None, user_id=0):
        """Return KPI data for the 4 cards, based on filters."""
        # Fallback to current month if dates aren’t provided
        from datetime import date as _date
        today = _date.today()
        first_day = _date(today.year, today.month, 1)

        date_from = date_from or first_day.strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')

        try:
            user_id = self._effective_user_id(user_id)
        except Exception:
            user_id = 0

        # kpis = request.env['tti.cs.dashboard'].sudo().get_kpis(date_from, date_to, user_id)
        # return kpis

        cid, _company = self._get_active_company()
        print(f"[CS DASH] /data active company_id={cid}")

        kpis = self._dash_env().get_kpis(date_from, date_to, user_id, cid)
        return kpis

    @http.route('/tti_cs_dashboard/report_status', type='json', auth='user')
    def get_report_status(self, date_from=None, date_to=None, user_id=0):
        """Return report delivery stats for Donut + Table + Bar sections."""
        from datetime import date as _date
        today = _date.today()
        first_day = _date(today.year, today.month, 1)

        date_from = date_from or first_day.strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')

        try:
            user_id = self._effective_user_id(user_id)
        except Exception:
            user_id = 0

        # dashboard = request.env['tti.cs.dashboard'].sudo()
        # print(f"[CS DASH] ▶ /report_status called df={date_from} dt={date_to} user={user_id}")
        # report_data = dashboard._get_report_status_summary(date_from, date_to, user_id)

        cid, _company = self._get_active_company()
        dashboard = self._dash_env()

        print(f"[CS DASH] ▶ /report_status called df={date_from} dt={date_to} user={user_id} company={cid}")
        report_data = dashboard._get_report_status_summary(date_from, date_to, user_id, cid)

        # Build table rows with percentages
        total = report_data.get('total', 0)

        def pct(n):
            return round((n / total) * 100, 1) if total else 0.0

        table_data = [
            {'name': 'Delivered Reports', 'count': report_data['delivered'], 'percent': pct(report_data['delivered'])},
            {'name': 'Late Reports', 'count': report_data['late'], 'percent': pct(report_data['late'])},
            {'name': 'Overdue Reports', 'count': report_data['overdue'], 'percent': pct(report_data['overdue'])},
            {'name': 'Pending Reports', 'count': report_data['pending'], 'percent': pct(report_data['pending'])},
        ]

        print(f"[CS DASH] ◀ /report_status result table={table_data}")
        return {
            'summary': report_data,
            'table_data': table_data,
        }

    @http.route('/tti_cs_dashboard/daily_summary', type='json', auth='user')
    def get_daily_summary(self, user_id=0):
        """Return daily activity table; only CS Personnel filter applies."""
        try:
            user_id = int(user_id or 0)
        except Exception:
            user_id = 0
        # rows = request.env['tti.cs.dashboard'].sudo()._get_daily_activity_summary(user_id)
        # return {'rows': rows}

        cid, _company = self._get_active_company()
        rows = self._dash_env()._get_daily_activity_summary(user_id, cid)
        return {'rows': rows}

    @http.route('/tti_cs_dashboard/right_status', type='json', auth='user')
    def get_right_status(self, date_from=None, date_to=None, user_id=0):
        from datetime import date as _date
        today = _date.today()
        first_day = _date(today.year, today.month, 1)

        date_from = date_from or first_day.strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')
        try:
            user_id = self._effective_user_id(user_id)
        except Exception:
            user_id = 0

        # summary = request.env['tti.cs.dashboard'].sudo()._get_so_status_summary(date_from, date_to, user_id)

        cid, _company = self._get_active_company()
        summary = self._dash_env()._get_so_status_summary(date_from, date_to, user_id, cid)

        # keep order consistent with chart labels
        labels = ["Finalised Sale Order", "Open Sale Order", "Sale Order in Process", "Cancelled Sale Orders"]
        data = [
            summary.get('finalised', 0),
            summary.get('open', 0),
            summary.get('in_process', 0),
            summary.get('cancelled', 0),
        ]
        return {'summary': summary, 'labels': labels, 'data': data}

    # @http.route('/tti_cs_dashboard/parcel_overview', type='json', auth='user')
    # def get_parcel_overview(self, user_id=0):
    #     """Return data for Parcel Overview stacked bar chart."""
    #     try:
    #         user_id = self._effective_user_id(user_id)
    #     except Exception:
    #         user_id = 0
    #
    #     dashboard = request.env['tti.cs.dashboard'].sudo()
    #     data = dashboard._get_parcel_overview(user_id)
    #
    #     # Prepare chart format
    #     labels = ["Parcels"]
    #     datasets = [
    #         {"label": "Parcel Received", "data": [data['received']]},
    #         {"label": "Open Parcels", "data": [data['open']]},
    #         {"label": "Total Parcels", "data": [data['total']]},
    #     ]
    #
    #     return {"labels": labels, "datasets": datasets, "summary": data}

    def _get_parcel_overview(self, date_from, date_to, user_id):
        """Bar chart counts driven by parcel.tti_date window.
           - Parcel Received = parcels (tti_date in range) that are linked to any SO
           - Open Parcels    = parcels (tti_date in range) NOT linked to any SO
           - Total Parcels   = received + open (i.e., all parcels with tti_date in range)
           Personnel scope (if chosen): parcels filtered by deliver_to_tti.user_id = user_id
        """
        from datetime import datetime, time
        uid = int(user_id or 0)

        # Normalize date window to full-day datetimes
        df_dt = fields.Datetime.to_string(datetime.combine(fields.Date.to_date(date_from), time.min))
        dt_dt = fields.Datetime.to_string(datetime.combine(fields.Date.to_date(date_to), time.max))

        P = self.env['tti.parcels']
        SO = self.env['sale.order']

        # (1) Parcels created in window (tti_date)
        parcel_domain = [('tti_date', '>=', df_dt), ('tti_date', '<=', dt_dt)]
        if uid:
            parcel_domain.append(('deliver_to_tti.user_id', '=', uid))
        parcels_in_window = P.search(parcel_domain)
        window_ids = set(parcels_in_window.ids)

        # (2) Of those parcels, which are linked to any SO?
        #     (no date limit on SO; relationship is the source of truth)
        linked_so = SO.search([('tti_parcel_id', 'in', list(window_ids))])
        linked_ids = set(linked_so.mapped('tti_parcel_id').ids) & window_ids

        # (3) Counts
        received = len(linked_ids)
        open_cnt = len(window_ids - linked_ids)
        total = received + open_cnt

        print(f"[CS DASH][BAR] PARCEL WINDOW df={df_dt} dt={dt_dt} uid={uid}")
        print(
            f"[CS DASH][BAR] Parcels in window={len(window_ids)} | Linked(received)={received} | Open={open_cnt} | Total={total}")

        return {'received': received, 'open': open_cnt, 'total': total}

    @http.route('/tti_cs_dashboard/parcel_overview', type='json', auth='user')
    def get_parcel_overview(self, date_from=None, date_to=None, user_id=0):
        from datetime import date as _date
        today = _date.today()
        first_day = _date(today.year, today.month, 1)

        date_from = date_from or first_day.strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')

        try:
            eff_user_id = self._effective_user_id(user_id)
        except Exception:
            eff_user_id = 0

        print(
            f"\n[CS DASH] ▶ /parcel_overview called | df={date_from} dt={date_to} | incoming_user_id={user_id} | eff_user_id={eff_user_id}")

        # dashboard = request.env['tti.cs.dashboard'].sudo()
        # data = dashboard._get_parcel_overview(date_from, date_to, eff_user_id)

        cid, _company = self._get_active_company()
        dashboard = self._dash_env()

        data = dashboard._get_parcel_overview(date_from, date_to, eff_user_id, cid)

        labels = ["Parcels"]
        datasets = [
            {"label": "Parcel Received", "data": [data['received']]},
            {"label": "Open Parcels", "data": [data['open']]},
            {"label": "Total Parcels", "data": [data['total']]},
        ]

        print(f"[CS DASH] ◀ /parcel_overview result | datasets={datasets} | summary={data}\n")
        return {"labels": labels, "datasets": datasets, "summary": data}

    @http.route('/tti_cs_dashboard/person_grid', type='json', auth='user')
    def get_person_grid(self, date_from=None, date_to=None, user_id=0):
        from datetime import date as _date
        today = _date.today()
        first_day = _date(today.year, today.month, 1)

        date_from = date_from or first_day.strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')

        try:
            user_id = self._effective_user_id(user_id)
        except Exception:
            user_id = 0

        # data = request.env['tti.cs.dashboard'].sudo()._get_userwise_cards(date_from, date_to, user_id)

        cid, _company = self._get_active_company()
        data = self._dash_env()._get_userwise_cards(date_from, date_to, user_id, cid)

        # Front-end needs labels and values per card (we’ll compute in JS)
        return {'people': data}
