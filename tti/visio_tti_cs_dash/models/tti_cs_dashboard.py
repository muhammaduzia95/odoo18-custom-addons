# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_cs_dash\models\tti_cs_dashboard.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, timedelta, datetime, time


class TTICSDashboard(models.Model):
    _name = "tti.cs.dashboard"
    _description = "TTI Customer Service Dashboard"

    # =======================================
    # MAIN ENTRY POINT
    # =======================================
    @api.model
    # def get_kpis(self, date_from, date_to, user_id):
    def get_kpis(self, date_from, date_to, user_id, company_id):
        """Aggregate KPIs for the 4 sample cards."""
        return {
            'outsourced': self._get_outsourced_samples(date_from, date_to, user_id, company_id),
            'express': self._get_express_samples(date_from, date_to, user_id, company_id),
            'shuttle': self._get_shuttle_samples(date_from, date_to, user_id, company_id),
            'regular': self._get_regular_samples(date_from, date_to, user_id, company_id),
        }

    # =======================================
    # KPI METHODS
    # =======================================

    def _base_domain(self, date_from, date_to, user_id, company_id):
        """Reusable base domain for confirmed sale orders."""
        # domain = [
        #     ('state', '=', 'sale'),
        #     ('date_order', '>=', date_from),
        #     ('date_order', '<=', date_to),
        # ]
        domain = [
            ('state', '=', 'sale'),
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('company_id', '=', company_id),
        ]
        if user_id and int(user_id) != 0:
            domain.append(('user_id', '=', int(user_id)))
        return domain

    def _get_outsourced_samples(self, date_from, date_to, user_id, company_id):
        """Count of confirmed Sale Orders with Out Sourced Sample."""
        domain = self._base_domain(date_from, date_to, user_id, company_id) + [
            ('out_sourced_sample_id', '!=', False)
        ]
        return self.env['sale.order'].search_count(domain)

    def _get_express_samples(self, date_from, date_to, user_id, company_id):
        """Count of confirmed Sale Orders with Express Charges > 0."""
        domain = self._base_domain(date_from, date_to, user_id, company_id) + [
            ('tti_express_charges', '>', 0)
        ]
        return self.env['sale.order'].search_count(domain)

    def _get_shuttle_samples(self, date_from, date_to, user_id, company_id):
        """Count of confirmed Sale Orders with Shuttle Charges > 0."""
        domain = self._base_domain(date_from, date_to, user_id, company_id) + [
            ('tti_shuttle_service_charges', '>', 0)
        ]
        return self.env['sale.order'].search_count(domain)

    def _get_regular_samples(self, date_from, date_to, user_id, company_id):
        """Count of confirmed Sale Orders that are NOT express or shuttle."""
        domain = self._base_domain(date_from, date_to, user_id, company_id) + [
            ('tti_express_charges', '=', 0),
            ('tti_shuttle_service_charges', '=', 0)
        ]
        return self.env['sale.order'].search_count(domain)

    # -------------------------------------------------------------------------
    #  REPORT DELIVERY STATUS METHODS
    # -------------------------------------------------------------------------

    def _get_delivered_reports(self, date_from, date_to, user_id, company_id):
        """Reports sent on or before commitment_date."""
        # domain = [
        #     ('report_sent', '=', True),
        #     ('date_order', '>=', date_from),
        #     ('date_order', '<=', date_to),
        # ]
        domain = [
            ('report_sent', '=', True),
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('company_id', '=', company_id),
        ]
        if user_id and int(user_id) != 0:
            domain.append(('user_id', '=', int(user_id)))

        orders = self.env['sale.order'].search(domain)
        count = 0
        for so in orders:
            send_date = getattr(so, 'report_sent_date', so.write_date)
            if send_date and so.commitment_date and send_date.date() <= so.commitment_date.date():
                count += 1
        return count

    def _get_late_reports(self, date_from, date_to, user_id, company_id):
        """Reports sent after commitment_date."""
        # domain = [
        #     ('report_sent', '=', True),
        #     ('date_order', '>=', date_from),
        #     ('date_order', '<=', date_to),
        # ]
        domain = [
            ('report_sent', '=', True),
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('company_id', '=', company_id),
        ]
        if user_id and int(user_id) != 0:
            domain.append(('user_id', '=', int(user_id)))

        orders = self.env['sale.order'].search(domain)
        count = 0
        for so in orders:
            send_date = getattr(so, 'report_sent_date', so.write_date)
            if send_date and so.commitment_date and send_date.date() > so.commitment_date.date():
                count += 1
        return count

    def _get_overdue_reports(self, date_from, date_to, user_id, company_id):
        """Reports not sent and commitment_date has already passed."""
        today = date.today()
        domain = [
            ('report_sent', '=', False),
            ('commitment_date', '<', today),
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('company_id', '=', company_id),
        ]
        if user_id and int(user_id) != 0:
            domain.append(('user_id', '=', int(user_id)))

        return self.env['sale.order'].search_count(domain)

    # def _get_pending_reports(self, date_from, date_to, user_id):
    #     """Reports not sent but still within commitment_date."""
    #     today = date.today()
    #     domain = [
    #         ('report_sent', '=', False),
    #         ('commitment_date', '>=', today),
    #         ('date_order', '>=', date_from),
    #         ('date_order', '<=', date_to),
    #     ]
    #     if user_id and int(user_id) != 0:
    #         domain.append(('user_id', '=', int(user_id)))
    #
    #     return self.env['sale.order'].search_count(domain)

    def _get_pending_reports(self, date_from, date_to, user_id, company_id):
        today = fields.Date.context_today(self)
        domain = [
            ('report_sent', '=', False),
            ('commitment_date', '>=', today),
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('company_id', '=', company_id),
        ]
        if user_id and int(user_id) != 0:
            domain.append(('user_id', '=', int(user_id)))

        cnt = self.env['sale.order'].search_count(domain)
        print(
            f"[CS DASH][LEFT] Pending count={cnt} | user={user_id} | range={date_from}→{date_to} | today={today} | domain={domain}")
        return cnt

    # def _get_report_status_summary(self, date_from, date_to, user_id):
    #     delivered = self._get_delivered_reports(date_from, date_to, user_id)
    #     late = self._get_late_reports(date_from, date_to, user_id)
    #     overdue = self._get_overdue_reports(date_from, date_to, user_id)
    #     pending = self._get_pending_reports(date_from, date_to, user_id)
    #     total = delivered + late + overdue + pending
    #     print(
    #         f"[CS DASH][LEFT] Donut totals → Delivered={delivered}, Late={late}, Overdue={overdue}, Pending={pending}, Total={total}")
    #     return {'delivered': delivered, 'late': late, 'overdue': overdue, 'pending': pending, 'total': total}

    # -------------------------------------------------------------------------
    #  COMBINED REPORT SUMMARY
    # -------------------------------------------------------------------------

    def _get_report_status_summary(self, date_from, date_to, user_id, company_id):
        """Returns all four counts + total in one dict."""
        delivered = self._get_delivered_reports(date_from, date_to, user_id, company_id)
        late = self._get_late_reports(date_from, date_to, user_id, company_id)
        overdue = self._get_overdue_reports(date_from, date_to, user_id, company_id)
        pending = self._get_pending_reports(date_from, date_to, user_id, company_id)

        total = delivered + late + overdue + pending

        return {
            'delivered': delivered,
            'late': late,
            'overdue': overdue,
            'pending': pending,
            'total': total,
        }

    # ================================
    # DAILY ACTIVITY (personnel-only)
    # ================================
    @api.model
    def _get_daily_activity_summary(self, user_id, company_id):
        """
        Build rows with Today / Yesterday / Day Before counts.
        Only CS Personnel (user_id) filter applies.
        """
        # Resolve user filter (0 = All)
        uid = int(user_id or 0)

        # Date buckets
        today = date.today()
        yest = today - timedelta(days=1)
        dayb = today - timedelta(days=2)

        def day_range(d):
            start_dt = datetime.combine(d, time.min)
            end_dt = datetime.combine(d, time.max)
            return fields.Datetime.to_string(start_dt), fields.Datetime.to_string(end_dt)

        def so_user_domain():
            return [('user_id', '=', uid)] if uid else []

        def parcel_user_domain():
            # attribute open parcels by deliver_to_tti.user_id = uid when filtering by user
            # (hr.employee.user_id is the common link)
            if not uid:
                return []
            return [('deliver_to_tti.user_id', '=', uid)]

        # ---------- helpers per metric ----------
        def count_parcels_received(day_):
            # distinct parcels linked via SO.m2m tti_parcel_id, bucket by parcel.create_date day
            start, end = day_range(day_)
            # so_domain = so_user_domain()
            so_domain = [('company_id', '=', company_id)] + so_user_domain()
            # read parcels through sale.order link
            orders = self.env['sale.order'].search(so_domain)
            parcels = orders.mapped('tti_parcel_id')
            if not parcels:
                return 0
            parcel_domain = [
                ('id', 'in', parcels.ids),
                ('create_date', '>=', start),
                ('create_date', '<=', end),
            ]
            if 'company_id' in self.env['tti.parcels']._fields:
                parcel_domain.append(('company_id', '=', company_id))
            return self.env['tti.parcels'].search_count(parcel_domain)

        def count_so_confirmed(day_):
            start, end = day_range(day_)
            domain = [
                         ('state', '=', 'sale'),
                         ('date_order', '>=', start),
                         ('date_order', '<=', end),
                         ('company_id', '=', company_id),
                     ] + so_user_domain()
            return self.env['sale.order'].search_count(domain)

        def count_open_parcels(day_):
            # parcels NOT attached to any sale order
            start, end = day_range(day_)
            # all parcel ids that appear on any SO.m2m tti_parcel_id
            # linked_ids = set(self.env['sale.order'].search([]).mapped('tti_parcel_id').ids)
            linked_ids = set(
                self.env['sale.order'].search([('company_id', '=', company_id)]).mapped('tti_parcel_id').ids)
            dom = [
                      ('create_date', '>=', start),
                      ('create_date', '<=', end),
                  ] + parcel_user_domain()
            if 'company_id' in self.env['tti.parcels']._fields:
                dom.append(('company_id', '=', company_id))
            if linked_ids:
                dom.append(('id', 'not in', list(linked_ids)))
            return self.env['tti.parcels'].search_count(dom)

        def count_so_in_process(day_):
            # SO with (no invoice fully posted) OR (report_sent = False), bucket by date_order day
            start, end = day_range(day_)
            domain = [
                         ('date_order', '>=', start),
                         ('date_order', '<=', end),
                         ('company_id', '=', company_id),
                     ] + so_user_domain()

            orders = self.env['sale.order'].search(domain)
            cnt = 0
            for so in orders:
                # fast path via invoice_status if available (standard Odoo)
                no_full_invoice = getattr(so, 'invoice_status', 'no') != 'invoiced'
                no_report = not getattr(so, 'report_sent', False)
                if no_full_invoice or no_report:
                    cnt += 1
            return cnt

        def count_delivered_reports(day_):
            # report_sent True; bucket by report_sent_date (fallback write_date)
            start, end = day_range(day_)
            # domain = [('report_sent', '=', True)] + so_user_domain()
            domain = [('report_sent', '=', True), ('company_id', '=', company_id)] + so_user_domain()
            orders = self.env['sale.order'].search(domain)
            cnt = 0
            for so in orders:
                send_dt = getattr(so, 'report_sent_date', so.write_date)
                if send_dt and start <= fields.Datetime.to_string(send_dt) <= end:
                    cnt += 1
            return cnt

        def count_pending_reports(day_):
            # snapshot per day using SO date_order bucket: unsent & commitment_date >= that day’s date
            start, end = day_range(day_)
            d = day_
            domain = [
                         ('report_sent', '=', False),
                         ('commitment_date', '>=', fields.Datetime.to_datetime(fields.Date.to_string(d))),
                         ('date_order', '>=', start),
                         ('date_order', '<=', end),
                         ('company_id', '=', company_id),
                     ] + so_user_domain()
            return self.env['sale.order'].search_count(domain)

        def count_late_reports(day_):
            # unsent and commitment_date < that day’s date; bucket by SO date_order day
            start, end = day_range(day_)
            d = day_
            domain = [
                         ('report_sent', '=', False),
                         ('commitment_date', '<', fields.Datetime.to_datetime(fields.Date.to_string(d))),
                         ('date_order', '>=', start),
                         ('date_order', '<=', end),
                         ('company_id', '=', company_id),
                     ] + so_user_domain()
            return self.env['sale.order'].search_count(domain)

        def row(name, f):
            return {
                'name': name,
                'today': f(today),
                'yesterday': f(yest),
                'day_before': f(dayb),
            }

        rows = [
            row('Parcels Received', count_parcels_received),
            row('Number of Sale Order Generated', count_so_confirmed),
            row('Open Parcels', count_open_parcels),
            row('Sale Orders In Process', count_so_in_process),
            row('Delivered Reports', count_delivered_reports),
            row('Pending Reports', count_pending_reports),
            row('Late Reports', count_late_reports),
        ]
        return rows

    # --- RIGHT DONUT (SO status) ---
    def _get_so_status_summary(self, date_from, date_to, user_id, company_id):
        """Finalised / Open / In-Process / Cancelled counts (by SO date_order)."""
        base = [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('company_id', '=', company_id),

        ]
        if user_id and int(user_id) != 0:
            base.append(('user_id', '=', int(user_id)))

        so = self.env['sale.order'].search(base)

        finalised = sum(1 for s in so if s.state == 'sale')
        open_so = sum(1 for s in so if s.state in ('draft', 'sent'))
        cancelled = sum(1 for s in so if s.state == 'cancel')

        # In process: has at least one POSTED invoice, but report not sent
        in_process = 0
        if so:
            # prefetch lines to reduce queries
            so.mapped('order_line.invoice_lines.move_id')
        for s in so:
            if not getattr(s, 'report_sent', False):
                # any posted customer invoice linked?
                has_posted_invoice = any(
                    mv.state == 'posted' and mv.move_type == 'out_invoice'
                    for mv in s.order_line.mapped('invoice_lines.move_id')
                )
                if has_posted_invoice:
                    in_process += 1

        return {
            'finalised': finalised,
            'open': open_so,
            'in_process': in_process,
            'cancelled': cancelled,
        }

    # --- Parcel status ---
    # def _get_parcel_overview(self, user_id):
    #     """Counts for Parcel Received (linked to SO), Open Parcels (not linked), Total Parcels.
    #     Only CS Personnel (deliver_to_tti.user_id) filter applies.
    #     """
    #     uid = int(user_id or 0)
    #
    #     parcels_model = self.env['tti.parcels']
    #     so_model = self.env['sale.order']
    #
    #     # All parcels for this CS personnel (or all if uid=0)
    #     parcel_domain = []
    #     if uid:
    #         parcel_domain.append(('deliver_to_tti.user_id', '=', uid))
    #     total_all = parcels_model.search_count(parcel_domain)
    #
    #     # Parcels that appear on any SO.m2m tti_parcel_id (respect personnel if given)
    #     so_domain = []
    #     if uid:
    #         so_domain.append(('user_id', '=', uid))
    #     linked_parcel_ids = set(so_model.search(so_domain).mapped('tti_parcel_id').ids)
    #
    #     if uid:
    #         # Intersect with this personnel’s parcels
    #         user_parcel_ids = set(parcels_model.search(parcel_domain).ids)
    #         linked_parcel_ids = linked_parcel_ids & user_parcel_ids
    #
    #     received = len(linked_parcel_ids)
    #     open_p = max(total_all - received, 0)
    #
    #     return {
    #         'received': received,
    #         'open': open_p,
    #         'total': received + open_p,
    #     }

    # def _get_parcel_overview(self, date_from, date_to, user_id):
    #     """Counts for Parcel Received (linked), Open (not linked), Total — all scoped by parcel.create_date in [date_from, date_to] and optional personnel."""
    #     uid = int(user_id or 0)
    #
    #     print("\n[CS DASH][BAR] Building Parcel Overview (date-scoped)")
    #     print(f"[CS DASH][BAR] user_id={uid} | date_from={date_from} | date_to={date_to}")
    #
    #     parcels_model = self.env['tti.parcels']
    #     so_model = self.env['sale.order']
    #
    #     df_dt = fields.Datetime.to_string(datetime.combine(
    #         fields.Date.to_date(date_from), time.min))
    #     dt_dt = fields.Datetime.to_string(datetime.combine(
    #         fields.Date.to_date(date_to), time.max))
    #
    #     # 1) Parcels in date window (+ optional personnel)
    #     parcel_domain = [
    #         ('create_date', '>=', df_dt),
    #         ('create_date', '<=', dt_dt),
    #     ]
    #     if uid:
    #         parcel_domain.append(('deliver_to_tti.user_id', '=', uid))
    #     print(f"[CS DASH][BAR] parcel_domain={parcel_domain}")
    #
    #     parcels_in_range = parcels_model.search(parcel_domain)
    #     parcels_in_range_ids = set(parcels_in_range.ids)
    #     total_all = len(parcels_in_range_ids)
    #     print(f"[CS DASH][BAR] Parcels in range = {total_all}")
    #
    #     # 2) SOs (optional personnel + optional SO date filter if you want tighter linkage)
    #     so_domain = []
    #     if uid:
    #         so_domain.append(('user_id', '=', uid))
    #     # (optional) also scope by SO date window; comment out if not desired:
    #     so_domain += [('date_order', '>=', date_from), ('date_order', '<=', date_to)]
    #     print(f"[CS DASH][BAR] so_domain={so_domain}")
    #
    #     linked_parcel_ids = set(so_model.search(so_domain).mapped('tti_parcel_id').ids)
    #     # count only the linked parcels that are also inside the parcel date window
    #     linked_in_window = linked_parcel_ids & parcels_in_range_ids
    #     received = len(linked_in_window)
    #     open_p = max(total_all - received, 0)
    #     total_calc = received + open_p
    #
    #     print(f"[CS DASH][BAR] Summary (date-scoped) → Received={received}, Open={open_p}, Total={total_calc}\n")
    #
    #     return {
    #         'received': received,
    #         'open': open_p,
    #         'total': total_calc,
    #     }

    def _get_parcel_overview(self, date_from, date_to, user_id, company_id):
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
        if 'company_id' in P._fields:
            parcel_domain.append(('company_id', '=', company_id))
        parcels_in_window = P.search(parcel_domain)
        window_ids = set(parcels_in_window.ids)

        # (2) Of those parcels, which are linked to any SO?
        #     (no date limit on SO; relationship is the source of truth)
        # linked_so = SO.search([('tti_parcel_id', 'in', list(window_ids))])
        linked_so = SO.search([('tti_parcel_id', 'in', list(window_ids)), ('company_id', '=', company_id)])
        linked_ids = set(linked_so.mapped('tti_parcel_id').ids) & window_ids

        # (3) Counts
        received = len(linked_ids)
        open_cnt = len(window_ids - linked_ids)
        total = received + open_cnt

        print(f"[CS DASH][BAR] PARCEL WINDOW df={df_dt} dt={dt_dt} uid={uid}")
        print(
            f"[CS DASH][BAR] Parcels in window={len(window_ids)} | Linked(received)={received} | Open={open_cnt} | Total={total}")

        return {'received': received, 'open': open_cnt, 'total': total}

    # --- SALES-PERSON WISE DONUT CARDS ---
    def _get_userwise_cards(self, date_from, date_to, selected_user_id=0, company_id=False):
        """
        For each CS user (or only selected), return:
          - Report Delivered (report_sent True and send_date <= commitment_date)
          - Reports Due     (report_sent False and commitment_date < today)
          - Parcel Assigned (parcels linked to SOs)
          - Open Parcels    (parcels for that user not linked to any SO)
        All counts are scoped to [date_from, date_to] by SO.date_order and parcel.create_date.
        """
        uid_filter = int(selected_user_id or 0)
        today = date.today()

        # Which users to include (those with SO in range OR specific user)
        so_domain = [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('company_id', '=', company_id),

        ]
        if uid_filter:
            so_domain += [('user_id', '=', uid_filter)]

        orders = self.env['sale.order'].search(so_domain)
        users = orders.mapped('user_id')
        if uid_filter and users:
            users = users.filtered(lambda u: u.id == uid_filter)

        # Precompute parcels linkage
        # Map user_id -> set(parcel_ids linked via SO)
        user_linked_parcel_ids = {}
        for u in users:
            u_orders = orders.filtered(lambda s: s.user_id.id == u.id)
            user_linked_parcel_ids[u.id] = set(u_orders.mapped('tti_parcel_id').ids)

        # For open/assigned parcels we scope to parcel.create_date within range
        def parcel_ids_for_user(u):
            dom = [('create_date', '>=', date_from), ('create_date', '<=', date_to)]
            dom += [('deliver_to_tti.user_id', '=', u.id)]
            if 'company_id' in self.env['tti.parcels']._fields:
                dom.append(('company_id', '=', company_id))
            return set(self.env['tti.parcels'].search(dom).ids)

        rows = []
        for u in users.sorted(lambda x: (x.name or '').lower()):
            u_orders = orders.filtered(lambda s: s.user_id.id == u.id)

            # Delivered
            delivered = 0
            for so in u_orders.filtered(lambda s: s.report_sent):
                send_dt = getattr(so, 'report_sent_date', so.write_date)
                if so.commitment_date and send_dt and send_dt.date() <= so.commitment_date.date():
                    delivered += 1

            # Due (unsent & overdue)
            due = self.env['sale.order'].search_count([
                ('user_id', '=', u.id),
                ('report_sent', '=', False),
                ('commitment_date', '<', today),
                ('date_order', '>=', date_from),
                ('date_order', '<=', date_to),
                ('company_id', '=', company_id),

            ])

            # Parcels
            all_user_parcels = parcel_ids_for_user(u)
            assigned_ids = user_linked_parcel_ids.get(u.id, set()) & all_user_parcels
            open_ids = all_user_parcels - assigned_ids

            rows.append({
                'user_id': u.id,
                'name': u.name,
                'delivered': delivered,
                'due': due,
                'assigned': len(assigned_ids),
                'open': len(open_ids),
            })
        return rows
