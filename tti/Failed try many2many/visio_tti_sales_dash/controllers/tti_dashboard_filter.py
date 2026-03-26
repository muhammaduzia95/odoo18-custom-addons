# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_sales_dash\controllers\tti_dashboard_filter.py
# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from calendar import monthrange
from odoo.exceptions import UserError
from datetime import date
import calendar


class TTISalesDashCtl(http.Controller):

    @http.route('/tti_sales_dashboard/filters', type='json', auth='user')
    def get_filters(self):
        # Periods as month names
        periods = [{'id': i, 'name': calendar.month_name[i]} for i in range(1, 13)]

        # Years from invoices/refunds, use invoice_date or accounting date
        request.env.cr.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM COALESCE(invoice_date, date))::int AS y
            FROM account_move
            WHERE move_type IN ('out_invoice','out_refund') AND state='posted'
            ORDER BY y
        """)
        years = [r[0] for r in request.env.cr.fetchall()]
        current_year = date.today().year
        if not years:
            years = [current_year]
        # expand to contiguous range; if single year, show last 5 years up to current
        if len(years) == 1:
            start = min(years[0], current_year) - 4
            years = list(range(start, current_year + 1))
        else:
            years = list(range(min(years), max(years) + 1))

        cats = [{'id': r['id'], 'name': r['name']}
                for r in request.env['tti.si.category'].sudo().search([]).read(['name'])]
        subs = [{'id': r['id'], 'name': r['name']}
                for r in request.env['tti.si.sub.category'].sudo().search([]).read(['name'])]
        zones = [{'id': r['id'], 'name': r['name']}
                 for r in request.env['tti.city.zone'].sudo().search([]).read(['name'])]

        # return {
        #     'years': years,
        #     'periods': periods,
        #     'categories': cats,
        #     'subcategories': subs,
        #     'zones': zones,
        # }

        current_date = date.today()
        return {
            'years': years,
            'periods': periods,
            'categories': cats,
            'subcategories': subs,
            'zones': zones,
            'default_from_period': current_date.month,
            'default_to_period': current_date.month,
            'default_from_year': current_date.year,
            'default_to_year': current_date.year,
        }

    @http.route('/tti_sales_dashboard/filter_data', type='json', auth='user')
    def get_data(self, **kw):
        p = kw.get('data', {}) or {}
        print(f"[FILTER_DATA] Incoming payload: {p} (types: from_period={type(p.get('from_period'))}, "
              f"to_period={type(p.get('to_period'))}, from_year={type(p.get('from_year'))}, "
              f"to_year={type(p.get('to_year'))}, category={type(p.get('category'))}, "
              f"subcategory={type(p.get('subcategory'))}, zone={type(p.get('zone'))})")

        def _as_int(val, default):
            # Accept browser 'null'/'none'/None/'' and fall back safely
            if val is None or val == '' or val == 'null' or val == 'none':
                return default
            try:
                return int(val)
            except Exception as ex:
                print(f"[FILTER_DATA] _as_int failed for value={val} ({type(val)}). Using default={default}. ex={ex}")
                return default

        today_year = date.today().year
        fp = _as_int(p.get('from_period'), 1)
        fy = _as_int(p.get('from_year'), today_year)
        tp = _as_int(p.get('to_period'), 12)
        ty = _as_int(p.get('to_year'), today_year)

        def _as_list(val):
            """Convert payload values to list of ints safely."""
            if not val or val in ('null', 'none', '[]', 'All', ''):
                return []
            if isinstance(val, (list, tuple)):
                result = []
                for v in val:
                    try:
                        iv = int(v)
                        result.append(iv)
                    except Exception:
                        continue
                return result
            try:
                return [int(val)]
            except Exception:
                return []

        # Optional filters as lists
        cat_ids = _as_list(p.get('category'))
        sub_ids = _as_list(p.get('subcategory'))
        zone_ids = _as_list(p.get('zone'))

        print(
            f"[FILTER_DATA] Parsed -> fp={fp}, fy={fy}, tp={tp}, ty={ty}, cat_ids={cat_ids}, sub_ids={sub_ids}, zone_ids={zone_ids}")

        # Validate the period range (raise popup via UserError)
        if fy > ty or (fy == ty and fp > tp):
            raise UserError("Invalid period range: ‘From’ is after ‘To’. Please correct the months/years.")

        try:
            date_from = date(fy, fp, 1)
            date_to = date(ty, tp, monthrange(ty, tp)[1])
        except Exception as ex:
            print(f"[FILTER_DATA] Bad date combination fy={fy}, fp={fp}, ty={ty}, tp={tp}: ex={ex}")
            raise UserError("Please select valid months/years.")

        print(f"[FILTER_DATA] Computed range: {date_from} -> {date_to}")
        return request.env['tti.dashboard'].sudo().get_kpis(
            date_from,
            date_to,
            cat_ids or [],
            sub_ids or [],
            zone_ids or []
        )

