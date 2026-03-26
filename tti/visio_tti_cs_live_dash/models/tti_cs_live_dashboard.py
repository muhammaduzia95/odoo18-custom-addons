# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_cs_live_dash\models\tti_cs_live_dashboard.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, datetime, time
import pytz


class TTICSLiveDashboard(models.Model):
    _name = "tti.cs.live.dashboard"
    _description = "TTI CS Live Dashboard (computations)"

    # =========================
    # Donut (already done)
    # =========================
    @api.model
    def get_report_delivery_status(self, date_from, date_to):
        print(f"[CS-LIVE] get_report_delivery_status() called with date_from={date_from}, date_to={date_to}")
        delivered = self._count_delivered_on_time(date_from, date_to)
        late = self._count_late_reports(date_from, date_to)
        pending = self._count_pending_reports(date_from, date_to)
        result = {'delivered': delivered, 'late': late, 'pending': pending, 'total': delivered + late + pending}
        print(f"[CS-LIVE] report_delivery_status result={result}")
        return result

    def _count_delivered_on_time(self, date_from, date_to):
        # domain = [('report_sent', '=', True), ('date_order', '>=', date_from), ('date_order', '<=', date_to)]
        domain = [('company_id', '=', self.env.company.id), ('report_sent', '=', True), ('date_order', '>=', date_from),
                  ('date_order', '<=', date_to)]
        print(f"[CS-LIVE] _count_delivered_on_time domain={domain}")
        orders = self.env['sale.order'].search(domain)
        cnt = 0
        for so in orders:
            send_dt = getattr(so, 'report_sent_date', so.write_date)
            if send_dt and so.commitment_date and send_dt.date() <= so.commitment_date.date():
                cnt += 1
        print(f"[CS-LIVE] _count_delivered_on_time count={cnt}")
        return cnt

    def _count_late_reports(self, date_from, date_to):
        # domain = [('report_sent', '=', True), ('date_order', '>=', date_from), ('date_order', '<=', date_to)]
        domain = [('company_id', '=', self.env.company.id), ('report_sent', '=', True), ('date_order', '>=', date_from),
                  ('date_order', '<=', date_to)]
        print(f"[CS-LIVE] _count_late_reports domain={domain}")
        orders = self.env['sale.order'].search(domain)
        cnt = 0
        for so in orders:
            send_dt = getattr(so, 'report_sent_date', so.write_date)
            if send_dt and so.commitment_date and send_dt.date() > so.commitment_date.date():
                cnt += 1
        print(f"[CS-LIVE] _count_late_reports count={cnt}")
        return cnt

    def _count_pending_reports(self, date_from, date_to):
        today = date.today()
        # domain = [
        #     ('report_sent', '=', False),
        #     ('commitment_date', '>=', today),
        #     ('date_order', '>=', date_from),
        #     ('date_order', '<=', date_to),
        # ]
        domain = [
            ('company_id', '=', self.env.company.id),
            ('report_sent', '=', False),
            ('commitment_date', '>=', today),
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
        ]
        print(f"[CS-LIVE] _count_pending_reports domain={domain}")
        cnt = self.env['sale.order'].search_count(domain)
        print(f"[CS-LIVE] _count_pending_reports count={cnt}")
        return cnt

    # =======================================
    # Reports Due Today (table, left-bottom)
    # =======================================
    def _format_hms(self, seconds):
        """Return H:MM:SS from total seconds (no prefix)."""
        seconds = max(0, int(seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h}:{m:02d}:{s:02d}"

    @api.model
    def get_reports_due_today(self):
        """
        Unsent SOs with commitment_date falling on *today* in user's timezone.
        Return rows sorted by absolute time-to-due ascending.
        due_in is displayed as H:MM:SS (no prefixes).
        """
        user = self.env.user
        user_tz = pytz.timezone(user.tz or 'UTC')

        # Now in UTC and converted to user's tz
        now_utc = fields.Datetime.now()
        now_user = fields.Datetime.context_timestamp(self, now_utc)  # aware in user tz
        today_user = now_user.date()

        # Build user-local day's start/end, convert to UTC for domain
        start_user = user_tz.localize(datetime.combine(today_user, time.min))
        end_user = user_tz.localize(datetime.combine(today_user, time.max))
        start_utc = start_user.astimezone(pytz.UTC)
        end_utc = end_user.astimezone(pytz.UTC)

        start_utc_s = fields.Datetime.to_string(start_utc)
        end_utc_s = fields.Datetime.to_string(end_utc)

        # domain = [
        #     ('report_sent', '=', False),
        #     ('commitment_date', '>=', start_utc_s),
        #     ('commitment_date', '<=', end_utc_s),
        # ]
        domain = [
            ('company_id', '=', self.env.company.id),
            ('report_sent', '=', False),
            ('commitment_date', '>=', start_utc_s),
            ('commitment_date', '<=', end_utc_s),
        ]
        print(f"[CS-LIVE] get_reports_due_today domain={domain} (user_tz={user.tz})")

        orders = self.env['sale.order'].search(domain, order='commitment_date asc')

        # Build unsorted rows with raw seconds
        raw_rows = []
        for so in orders:
            if not so.commitment_date:
                continue
            commit_user = fields.Datetime.context_timestamp(self, so.commitment_date)
            if not commit_user:
                continue
            delta = commit_user - now_user
            seconds = int(delta.total_seconds())
            raw_rows.append({
                'report_no': so.name or '',
                'due_seconds': seconds,  # signed (negative = overdue)
                'overdue': seconds < 0,
            })

        # Sort by absolute due time ascending (closest first)
        raw_rows.sort(key=lambda r: abs(r['due_seconds']))

        # Re-number sr and format due_in as H:MM:SS
        rows = []
        for idx, r in enumerate(raw_rows, start=1):
            rows.append({
                'sr': idx,
                'report_no': r['report_no'],
                'due_in': self._format_hms(abs(r['due_seconds'])),  # e.g., 3:23:00
                'due_seconds': r['due_seconds'],
                'overdue': r['overdue'],
            })

        print(f"[CS-LIVE] get_reports_due_today rows_built={len(rows)} (sorted by abs seconds)")
        return rows

    # Utility to format seconds -> "in 2h 15m" or "Overdue by 1h 03m"
    def _format_duration(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m:02d}m"
        else:
            return f"{m}m"

    # ---------------- RIGHT TABLE: respects date range ----------------
    @api.model
    def get_right_person_summary(self, date_from, date_to):
        """
        For each salesperson with activity in the range:
          - parcel_assigned: parcels created in range for that user AND linked to that user's SOs in range
          - open_parcels: parcels created in range for that user NOT linked to any SO
          - reports_due: SOs in range with report_sent=False AND commitment_date < end_of_range
          - reports_delivered: SOs in range with report_sent=True AND send_date <= commitment_date
        """
        user = self.env.user
        user_tz = pytz.timezone(user.tz or 'UTC')

        # Build user-local day bounds for the given date strings, then convert to UTC
        # Lower bound: date_from 00:00:00 (user tz) → UTC; Upper bound: date_to 23:59:59 (user tz) → UTC
        df = datetime.strptime(date_from, '%Y-%m-%d').date()
        dt = datetime.strptime(date_to, '%Y-%m-%d').date()
        start_user = user_tz.localize(datetime.combine(df, time.min))
        end_user = user_tz.localize(datetime.combine(dt, time.max))
        start_utc = start_user.astimezone(pytz.UTC)
        end_utc = end_user.astimezone(pytz.UTC)
        start_utc_s = fields.Datetime.to_string(start_utc)
        end_utc_s = fields.Datetime.to_string(end_utc)

        print(f"[CS-LIVE] get_right_person_summary tz={user.tz} start={start_utc_s} end={end_utc_s}")

        so_model = self.env['sale.order']
        parcel_model = self.env['tti.parcels']

        # SOs in range
        # so_range = so_model.search([('date_order', '>=', start_utc_s), ('date_order', '<=', end_utc_s)])
        so_range = so_model.search([('company_id', '=', self.env.company.id), ('date_order', '>=', start_utc_s),
                                    ('date_order', '<=', end_utc_s)])
        users = so_range.mapped('user_id')  # only users with activity in SOs

        rows = []
        sr = 1
        for u in users.sorted(lambda x: (x.name or '').lower()):
            u_orders = so_range.filtered(lambda s: s.user_id.id == u.id)

            # Parcels created in range for this user
            # parcels_range = parcel_model.search([
            #     ('create_date', '>=', start_utc_s),
            #     ('create_date', '<=', end_utc_s),
            #     ('deliver_to_tti.user_id', '=', u.id),
            # ])
            parcels_range = parcel_model.search([
                ('company_id', '=', self.env.company.id),
                ('create_date', '>=', start_utc_s),
                ('create_date', '<=', end_utc_s),
                ('deliver_to_tti.user_id', '=', u.id),
            ])
            parcels_ids = set(parcels_range.ids)

            # Parcels linked to this user's SOs IN RANGE
            linked_ids_all = set(u_orders.mapped('tti_parcel_id').ids)
            assigned_ids = linked_ids_all & parcels_ids
            open_ids = parcels_ids - assigned_ids

            # Reports due (overdue unsent) with reference point = end of selected range
            # reports_due = so_model.search_count([
            #     ('user_id', '=', u.id),
            #     ('report_sent', '=', False),
            #     ('commitment_date', '<', end_utc_s),
            #     ('date_order', '>=', start_utc_s),
            #     ('date_order', '<=', end_utc_s),
            # ])
            reports_due = so_model.search_count([
                ('company_id', '=', self.env.company.id),
                ('user_id', '=', u.id),
                ('report_sent', '=', False),
                ('commitment_date', '<', end_utc_s),
                ('date_order', '>=', start_utc_s),
                ('date_order', '<=', end_utc_s),
            ])

            # Reports delivered on time in range
            delivered_cnt = 0
            for so in u_orders.filtered(lambda s: s.report_sent):
                send_dt = getattr(so, 'report_sent_date', so.write_date)
                if send_dt and so.commitment_date and send_dt <= so.commitment_date:
                    delivered_cnt += 1

            activity_total = len(assigned_ids) + len(open_ids) + reports_due + delivered_cnt
            if activity_total == 0:
                continue

            rows.append({
                'sr': sr,
                'name': u.name,
                'parcel_assigned': len(assigned_ids),
                'open_parcels': len(open_ids),
                'reports_due': reports_due,
                'reports_delivered': delivered_cnt,
            })
            sr += 1

        print(f"[CS-LIVE] get_right_person_summary rows_built={len(rows)}")
        return rows
