// D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_sales_dash\static\src\js\tti_dashboard.js

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";

const DASH_LOG_NS = "[TTI DASH]";

class TTIDashboard extends Component {
  static template = "TTIDashboardMain";

  formatM(v, digits = 2) {
    const n = Number(v) || 0;
    return (n / 1_000_000).toFixed(digits) + "M";
  }

  static props = {
  action: { type: Object, optional: true },
  actionId: { type: Number, optional: true },
  updateActionState: { type: Function, optional: true },
  globalState: { type: Object, optional: true },
  className: { type: String, optional: true },
};

  setup() {
  console.info(DASH_LOG_NS, "TTIDashboard setup() called with props:", this.props);

  // 🔹 Read saved filters from action.state (for breadcrumb back)
  this.savedFilters =
    (this.props.action &&
      this.props.action.state &&
      this.props.action.state.dashboardFilters) ||
    null;

  this.state = useState({
      periods: [],
      years: [],
      categories: [],
      subcategories: [],
      zones: [],
      from_period: null,
      from_year: null,
      to_period: null,
      to_year: null,
      category: "null",
      subcategory: "null",
      zone: "null",
      kpis: {
        total_sales: 0,
        total_recovery: 0,
        total_recovery_ids: [],
        recovered_pct: 0,
        pending_so: 0,
        pending_so_ids: [],
        open_quotations: 0,
        open_quotations_ids: [],
        mom_growth: 0,
        pop_growth: 0,
        yoy_growth: 0,
        samples_run: 0,
        samples_run_ids: [],
        pending_reports: 0,
        pending_reports_ids: [],
        reports_sent: 0,
        reports_sent_ids: [],
        top_clients: [],
        total_invoices: 0,
        total_invoices_ids: [],
        paid_invoices: 0,
        paid_invoice_ids: [],
        not_paid_invoices: 0,
        not_paid_invoice_ids: [],
        partial_invoices: 0,
        partial_invoice_ids: [],
        top_buyers: [],
        new_clients: 0,
        new_client_ids: [],
        new_brands: 0,
        new_brand_ids: [],

        lost_clients: 0,
        lost_client_ids: [],

        lost_brands: 0,
        lost_brand_ids: [],

        partner_pie: [],
        sales_line: { labels: [], series: [] },
        division_bar: { labels: [], series: [] },

        targets_achieved: [],
        targets_total_pct: 0,
        targets_only_total: false,
        targets_filters_applied: false,
      },
    });

    onMounted(async () => {
      console.info(DASH_LOG_NS, "Component mounted → loading filters & Chart.js");

      await this.loadFilters();

      // Don’t auto-fetch on mount; keep blank until all 4 selectors are set
      this.blankKPIsAndCharts();

      try {
        await loadJS("/web/static/lib/Chart/Chart.js");
        console.info(DASH_LOG_NS, "Chart.js loaded successfully");
      } catch (e) {
        console.warn(DASH_LOG_NS, "Chart.js failed to load", e);
      }
      // Initial render (blank)
      this.renderPartnerPie();
      this.renderSalesLine();
      this.renderDivisionBar();
    });
  }

  // ---------- small helpers ----------
  isEmptySel(v) {
    return v === "none" || v === "null" || v === null || v === undefined || v === "";
  }

  anyMissingRange() {
    const missing =
      this.isEmptySel(this.state.from_period) ||
      this.isEmptySel(this.state.to_period) ||
      this.isEmptySel(this.state.from_year) ||
      this.isEmptySel(this.state.to_year);

    if (missing) {
      console.debug(DASH_LOG_NS, "Range is incomplete:", {
        from_period: this.state.from_period,
        to_period: this.state.to_period,
        from_year: this.state.from_year,
        to_year: this.state.to_year,
      });
    }
    return missing;
  }

  blankKPIsAndCharts() {
    console.info(DASH_LOG_NS, "blankKPIsAndCharts() → resetting KPIs & charts");

    Object.assign(this.state.kpis, {
      total_sales: 0,
      total_sales_ids: [],
      total_recovery: 0,
      total_recovery_ids: [],
      recovered_pct: 0,
      pending_so: 0,
      pending_so_ids: [],
      open_quotations: 0,
      open_quotations_ids: [],
      mom_growth: 0,
      pop_growth: 0,
      yoy_growth: 0,
      samples_run: 0,
      samples_run_ids: [],
      pending_reports: 0,
      pending_reports_ids: [],
      reports_sent: 0,
      reports_sent_ids: [],
      top_clients: [],
      total_invoices: 0,
      total_invoices_ids: [],
      paid_invoices: 0,
      paid_invoice_ids: [],
      not_paid_invoices: 0,
      not_paid_invoice_ids: [],
      partial_invoices: 0,
      partial_invoice_ids: [],
      top_buyers: [],
      new_clients: 0,
      new_client_ids: [],
      new_brands: 0,
      new_brand_ids: [],

      lost_clients: 0,
      lost_client_ids: [],

      lost_brands: 0,
      lost_brand_ids: [],

      partner_pie: [],
      sales_line: { labels: [], series: [] },
      division_bar: { labels: [], series: [] },
      targets_achieved: [],
      targets_total_pct: 0,
      targets_filters_applied: false,
    });

    if (typeof window.Chart !== "undefined") {
      this.renderPartnerPie();
      this.renderSalesLine();
      this.renderDivisionBar();
    }
  }

  // -----------------------
  // Data & Filters
  // -----------------------
  async loadFilters() {
    console.group(DASH_LOG_NS, "loadFilters()");
    try {
      const f = await rpc("/tti_sales_dashboard/filters", {});
      console.debug(DASH_LOG_NS, "/filters response:", f);

      this.state.periods = f.periods || [];
this.state.years = f.years || [];
this.state.categories = f.categories || [];
this.state.subcategories = f.subcategories || [];
this.state.zones = f.zones || [];

// 1) Apply backend defaults
this.state.from_period = f.default_from_period;
this.state.to_period = f.default_to_period;
this.state.from_year = f.default_from_year;
this.state.to_year = f.default_to_year;
this.state.category = "null";
this.state.subcategory = "null";
this.state.zone = "null";

// 2) If we have saved filters from action.state (breadcrumb back) → override defaults
if (this.savedFilters) {
  console.info(DASH_LOG_NS, "Restoring filters from action.state:", this.savedFilters);

  this.state.from_period = this.savedFilters.from_period ?? this.state.from_period;
  this.state.to_period = this.savedFilters.to_period ?? this.state.to_period;
  this.state.from_year = this.savedFilters.from_year ?? this.state.from_year;
  this.state.to_year = this.savedFilters.to_year ?? this.state.to_year;

  this.state.category =
    this.savedFilters.category !== undefined ? this.savedFilters.category : this.state.category;
  this.state.subcategory =
    this.savedFilters.subcategory !== undefined
      ? this.savedFilters.subcategory
      : this.state.subcategory;
  this.state.zone =
    this.savedFilters.zone !== undefined ? this.savedFilters.zone : this.state.zone;
}

console.info(DASH_LOG_NS, "Filters initialized:", {
  from_period: this.state.from_period,
  to_period: this.state.to_period,
  from_year: this.state.from_year,
  to_year: this.state.to_year,
  category: this.state.category,
  subcategory: this.state.subcategory,
  zone: this.state.zone,
});

// 3) Load KPIs for whatever is now in state
await this.fetchData();

    } catch (e) {
      console.error(DASH_LOG_NS, "Error in loadFilters RPC:", e);
      const msg =
        (e && e.message) ||
        (e && e.data && e.data.message) ||
        (e && e.data && e.data.debug) ||
        "Unknown filters server error";
      window.alert("Error while loading dashboard filters:\n" + msg);
    } finally {
      console.groupEnd();
    }
  }

  async onFilterChange() {
    console.group(DASH_LOG_NS, "onFilterChange()");
    console.debug(DASH_LOG_NS, "Current state before validation:", {
      from_period: this.state.from_period,
      to_period: this.state.to_period,
      from_year: this.state.from_year,
      to_year: this.state.to_year,
      category: this.state.category,
      subcategory: this.state.subcategory,
      zone: this.state.zone,
    });

    // Only continue when ALL 4 range selectors are chosen
    if (this.anyMissingRange()) {
      console.info(DASH_LOG_NS, "Some range selectors are missing → blanking KPIs");
      // just clear KPIs, but don’t show an alert yet
      this.blankKPIsAndCharts();
      console.groupEnd();
      return;
    }

    const fp = Number(this.state.from_period);
    const tp = Number(this.state.to_period);
    const fy = Number(this.state.from_year);
    const ty = Number(this.state.to_year);

    console.debug(DASH_LOG_NS, "Parsed numeric range:", { fp, tp, fy, ty });

    // Now validate range only after all 4 are present
    if (fy > ty || (fy === ty && fp > tp)) {
      console.warn(
        DASH_LOG_NS,
        "Invalid period range detected in onFilterChange:",
        { fp, tp, fy, ty }
      );
      window.alert(
        "Invalid period range.\nFrom date is after To date.\nPlease correct Months/Years."
      );
      console.groupEnd();
      return;
    }

    console.info(DASH_LOG_NS, "Range valid → calling fetchData()");
    await this.fetchData();
    console.groupEnd();
  }

  // -----------------------
  // Charts
  // -----------------------
  renderPartnerPie() {
    const el = document.getElementById("partner_pie_chart");
    const data = this.state.kpis.partner_pie || [];
    console.debug(DASH_LOG_NS, "renderPartnerPie() called, data length:", data.length);

    if (!el || !window.Chart) {
      console.warn(
        DASH_LOG_NS,
        "renderPartnerPie() aborted: canvas or Chart.js missing",
        { hasElement: !!el, hasChart: !!window.Chart }
      );
      return;
    }

    if (this._partnerChart) {
      this._partnerChart.destroy();
      this._partnerChart = null;
    }

    // --- custom plugin to draw static labels on slices ---
    const staticLabelPlugin = {
      id: "staticSliceLabels",
      afterDatasetsDraw(chart, args, pluginOptions) {
        const { ctx } = chart;
        const dsMeta = chart.getDatasetMeta(0);
        if (!dsMeta || !dsMeta.data) return;

        ctx.save();
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        const fontSize = pluginOptions.fontSize || 12;
        const fontFamily = pluginOptions.fontFamily || "sans-serif";
        const fontWeight = pluginOptions.fontWeight || "700"; // ← bold
        const color = pluginOptions.color || "#111";
        const drawLabel = pluginOptions.drawLabel ?? false;

        ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`; // ← bold font
        ctx.fillStyle = color;

        dsMeta.data.forEach((arc, i) => {
          const p = arc.getCenterPoint ? arc.getCenterPoint() : arc.tooltipPosition();
          const value = chart.data.datasets[0].data[i];
          const label = chart.data.labels[i];
          const text = drawLabel ? `${label}: ${value}%` : `${value}%`;

          ctx.fillText(text, p.x, p.y);
        });

        ctx.restore();
      },
    };

    this._partnerChart = new Chart(el, {
      type: "pie",
      data: {
        labels: data.map((d) => d.label),
        datasets: [
          {
            data: data.map((d) => d.value), // already in %
            backgroundColor: ["#4e79a7", "#f28e2b", "#e15759"],
          },
        ],
      },
            options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
          // 🔴 Disable Chart.js tooltip completely for the pie
          tooltip: {
            enabled: false,
          },
          staticSliceLabels: {
            fontSize: 12,
            color: "#111",
            drawLabel: false,
          },
        },
      },

      plugins: [staticLabelPlugin],
    });
  }

  renderSalesLine() {
    const el = document.getElementById("sales_line_chart");
    const data = this.state.kpis.sales_line || { labels: [], series: [] };
    console.debug(DASH_LOG_NS, "renderSalesLine() called:", {
      labelCount: data.labels.length,
      seriesCount: (data.series || []).length,
    });

    if (!el || !window.Chart) {
      console.warn(
        DASH_LOG_NS,
        "renderSalesLine() aborted: canvas or Chart.js missing",
        { hasElement: !!el, hasChart: !!window.Chart }
      );
      return;
    }

    if (this._salesChart) {
      this._salesChart.destroy();
      this._salesChart = null;
    }

    this._salesChart = new Chart(el, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: (data.series || []).map((s) => ({
          label: s.label,
          data: s.data.map((v) => v / 1_000_000), // convert to millions
          fill: false,
          tension: 0.3,
        })),
      },
            options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
          // 🔴 Disable tooltip on line chart
          tooltip: {
            enabled: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (val) => val.toFixed(2) + "M",
            },
          },
        },
      },

    });
  }

  renderDivisionBar() {
    const el = document.getElementById("sales_bar_chart_right");
    const data = this.state.kpis.division_bar || { labels: [], series: [] };
    console.debug(DASH_LOG_NS, "renderDivisionBar() called:", {
      labelCount: data.labels.length,
      seriesCount: (data.series || []).length,
    });

    if (!el || !window.Chart) {
      console.warn(
        DASH_LOG_NS,
        "renderDivisionBar() aborted: canvas or Chart.js missing",
        { hasElement: !!el, hasChart: !!window.Chart }
      );
      return;
    }

    if (this._divisionChart) {
      this._divisionChart.destroy();
      this._divisionChart = null;
    }

    this._divisionChart = new Chart(el, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Sales by Division",
            data: data.series,
            backgroundColor: "#4e79a7",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          // 🔴 Disable tooltip on bar chart
          tooltip: {
            enabled: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (val) => (val / 1_000_000).toFixed(2) + "M",
            },
          },
        },
      },
    });
  }

  // -----------------------
  // Fetch Data
  // -----------------------
  async fetchData() {
    console.group(DASH_LOG_NS, "fetchData()");

    // Extra safety: stop here if somehow called with missing range
    if (this.anyMissingRange()) {
      console.info(DASH_LOG_NS, "fetchData() aborted due to missing range");
      this.blankKPIsAndCharts();
      console.groupEnd();
      return;
    }

    const asNumOr = (v, fb) => {
      if (v === "none" || v === "null" || v === null || v === undefined || v === "") return fb;
      const n = Number(v);
      return Number.isFinite(n) ? n : fb;
    };

    const nowYear = new Date().getFullYear();

    // Coerce everything to safe numbers ONLY after we know all 4 are present
    const fp = asNumOr(this.state.from_period, 1);
    const tp = asNumOr(this.state.to_period, 12);
    const fy = asNumOr(this.state.from_year, nowYear);
    const ty = asNumOr(this.state.to_year, nowYear);

    console.debug(DASH_LOG_NS, "Numeric range in fetchData:", { fp, tp, fy, ty });

    if (fy > ty || (fy === ty && fp > tp)) {
      console.warn(DASH_LOG_NS, "Invalid period range detected in fetchData:", {
        fp,
        tp,
        fy,
        ty,
      });
      window.alert(
        "Invalid period range.\nFrom date is after To date.\nPlease correct Months/Years."
      );
      console.groupEnd();
      return;
    }

    // ✅ Send ONLY the filters — no nested objects
    const payload = {
      from_period: fp,
      to_period: tp,
      from_year: fy,
      to_year: ty,
      category: this.state.category === "null" ? null : Number(this.state.category),
      subcategory:
        this.state.subcategory === "null" ? null : Number(this.state.subcategory),
      zone: this.state.zone === "null" ? null : Number(this.state.zone),
    };

    console.debug(DASH_LOG_NS, "Sending payload to /filter_data:", payload);

    let res;
    try {
      res = await rpc("/tti_sales_dashboard/filter_data", { data: payload });
      console.debug(DASH_LOG_NS, "/filter_data response received:", res);
    } catch (e) {
      console.error(DASH_LOG_NS, "Dashboard RPC failed:", e);
      const serverMsg =
        (e && e.message) ||
        (e && e.data && e.data.message) ||
        (e && e.data && e.data.debug) ||
        (e && e.data && e.data.name) ||
        "Unknown server error";
      window.alert("Server error:\n" + serverMsg);
      console.groupEnd();
      return;
    }

    Object.assign(this.state.kpis, {
      total_sales: res.total_sales ?? 0,
      total_sales_ids: Array.isArray(res.total_sales_ids) ? res.total_sales_ids : [],
      total_recovery: res.total_recovery ?? 0,
      total_recovery_ids: Array.isArray(res.total_recovery_ids)
        ? res.total_recovery_ids
        : [],
      recovered_pct: res.recovered_pct ?? 0,
      pending_so: res.pending_so ?? 0,
      pending_so_ids: Array.isArray(res.pending_so_ids) ? res.pending_so_ids : [],
      open_quotations: res.open_quotations ?? 0,
      open_quotations_ids: Array.isArray(res.open_quotations_ids)
        ? res.open_quotations_ids
        : [],
      mom_growth: res.mom_growth ?? 0,
      pop_growth: res.pop_growth ?? 0,
      yoy_growth: res.yoy_growth ?? 0,
      samples_run: res.samples_run ?? 0,
      samples_run_ids: Array.isArray(res.samples_run_ids) ? res.samples_run_ids : [],
      pending_reports: res.pending_reports ?? 0,
      pending_reports_ids: Array.isArray(res.pending_reports_ids)
        ? res.pending_reports_ids
        : [],
      reports_sent: res.reports_sent ?? 0,
      reports_sent_ids: Array.isArray(res.reports_sent_ids)
        ? res.reports_sent_ids
        : [],
      top_clients: Array.isArray(res.top_clients) ? res.top_clients : [],
      total_invoices: res.total_invoices ?? 0,
      total_invoices_ids: Array.isArray(res.total_invoices_ids)
        ? res.total_invoices_ids
        : [],
      paid_invoices: res.paid_invoices ?? 0,
      paid_invoice_ids: Array.isArray(res.paid_invoice_ids)
        ? res.paid_invoice_ids
        : [],

      not_paid_invoices: res.not_paid_invoices ?? 0,
      not_paid_invoice_ids: Array.isArray(res.not_paid_invoice_ids)
        ? res.not_paid_invoice_ids
        : [],

      partial_invoices: res.partial_invoices ?? 0,
      partial_invoice_ids: Array.isArray(res.partial_invoice_ids)
        ? res.partial_invoice_ids
        : [],

      top_buyers: Array.isArray(res.top_buyers) ? res.top_buyers : [],
      new_clients: res.new_clients ?? 0,
      new_client_ids: Array.isArray(res.new_client_ids) ? res.new_client_ids : [],
      new_brands: res.new_brands ?? 0,
      new_brand_ids: Array.isArray(res.new_brand_ids) ? res.new_brand_ids : [],

      lost_clients: res.lost_clients ?? 0,
      lost_client_ids: Array.isArray(res.lost_client_ids) ? res.lost_client_ids : [],

      lost_brands: res.lost_brands ?? 0,
      lost_brand_ids: Array.isArray(res.lost_brand_ids) ? res.lost_brand_ids : [],

      partner_pie: Array.isArray(res.partner_pie) ? res.partner_pie : [],
      sales_line: res.sales_line ?? { labels: [], series: [] },
      division_bar: res.division_bar ?? { labels: [], series: [] },
      targets_achieved: Array.isArray(res.targets_achieved)
        ? res.targets_achieved
        : [],
      targets_total_pct: res.targets_total_pct ?? 0,
      targets_filters_applied: res.targets_filters_applied ?? false,
    });

    console.info(DASH_LOG_NS, "KPI state updated; re-rendering charts");

if (typeof window.Chart !== "undefined") {
  this.renderPartnerPie();
  this.renderSalesLine();
  this.renderDivisionBar();
}

// 🔹 Persist filters in action.state so breadcrumb back restores them
if (this.props.updateActionState) {
  this.props.updateActionState({
    dashboardFilters: {
      from_period: this.state.from_period,
      to_period: this.state.to_period,
      from_year: this.state.from_year,
      to_year: this.state.to_year,
      category: this.state.category,
      subcategory: this.state.subcategory,
      zone: this.state.zone,
    },
  });
}

console.groupEnd();

  }

  // -----------------------
  // Drill Down Effect
  // -----------------------

  async openTotalSales() {
    console.log(DASH_LOG_NS, "openTotalSales() → IDs:", this.state.kpis.total_sales_ids);

    const ids = this.state.kpis.total_sales_ids || [];
    if (!ids.length) {
      window.alert("No invoices found for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "account.move",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      view_mode: "list,form",
      domain: [["id", "in", ids]],
      name: "Total Sales Invoices",
    });
  }

  async openTotalRecovery() {
    console.log(DASH_LOG_NS, "=== TOTAL RECOVERY CLICKED ===");
    console.log(DASH_LOG_NS, "total_recovery_ids =", this.state.kpis.total_recovery_ids);
    console.log(
      DASH_LOG_NS,
      "Count =",
      (this.state.kpis.total_recovery_ids || []).length
    );

    if (!this.state.kpis.total_recovery_ids || this.state.kpis.total_recovery_ids.length === 0) {
      window.alert("No recovered invoices found for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "account.move",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", this.state.kpis.total_recovery_ids]],
      name: "Total Recovery (Paid Invoices)",
    });
  }

  async openPendingSO() {
    console.log(DASH_LOG_NS, "=== PENDING SO CLICKED ===");
    console.log(DASH_LOG_NS, "pending_so_ids =", this.state.kpis.pending_so_ids);
    console.log(DASH_LOG_NS, "Count =", (this.state.kpis.pending_so_ids || []).length);

    if (!this.state.kpis.pending_so_ids || this.state.kpis.pending_so_ids.length === 0) {
      window.alert("No pending sale orders found for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "sale.order",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", this.state.kpis.pending_so_ids]],
      name: "Pending Sale Orders",
    });
  }

  async openOpenQuotations() {
    console.log(DASH_LOG_NS, "=== OPEN QUOTATIONS CLICKED ===");
    console.log(
      DASH_LOG_NS,
      "open_quotations_ids =",
      this.state.kpis.open_quotations_ids
    );
    console.log(
      DASH_LOG_NS,
      "Count =",
      (this.state.kpis.open_quotations_ids || []).length
    );

    if (
      !this.state.kpis.open_quotations_ids ||
      this.state.kpis.open_quotations_ids.length === 0
    ) {
      window.alert("No open quotations found for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "sale.order",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", this.state.kpis.open_quotations_ids]],
      name: "Open Quotations",
    });
  }

  async openSamplesRun() {
    console.log(DASH_LOG_NS, "=== SAMPLES RUN CLICKED ===");
    console.log(DASH_LOG_NS, "samples_run_ids =", this.state.kpis.samples_run_ids);
    console.log(DASH_LOG_NS, "Count =", (this.state.kpis.samples_run_ids || []).length);

    if (!this.state.kpis.samples_run_ids || this.state.kpis.samples_run_ids.length === 0) {
      window.alert("No Samples Run found for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "sale.order",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", this.state.kpis.samples_run_ids]],
      name: "Samples Run",
    });
  }

  async openPendingReports() {
    console.log(DASH_LOG_NS, "OPEN PENDING REPORTS → IDs:", this.state.kpis.pending_reports_ids);

    if (
      !this.state.kpis.pending_reports_ids ||
      this.state.kpis.pending_reports_ids.length === 0
    ) {
      window.alert("No Pending Reports found for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "sale.order",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", this.state.kpis.pending_reports_ids]],
      name: "Pending Reports",
    });
  }

  async openReportsSent() {
    console.log(DASH_LOG_NS, "OPEN REPORTS SENT → IDs:", this.state.kpis.reports_sent_ids);

    if (!this.state.kpis.reports_sent_ids || this.state.kpis.reports_sent_ids.length === 0) {
      window.alert("No reports sent found for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "account.move",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", this.state.kpis.reports_sent_ids]],
      name: "Reports Sent (Posted Invoices)",
    });
  }

  async openNewClients() {
    const ids = this.state.kpis.new_client_ids || [];
    console.log(DASH_LOG_NS, "OPEN NEW CLIENTS → IDs:", ids);
    console.log(DASH_LOG_NS, "Count:", ids.length);

    if (!ids.length) {
      window.alert("No new clients for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "res.partner",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", ids]],
      name: "New Clients",
    });
  }

  async openNewBrands() {
    console.log(DASH_LOG_NS, "OPEN NEW BRANDS → IDs:", this.state.kpis.new_brand_ids);

    if (!this.state.kpis.new_brand_ids || this.state.kpis.new_brand_ids.length === 0) {
      window.alert("No new brands for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "res.partner",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", this.state.kpis.new_brand_ids]],
      name: "New Brands",
    });
  }

  async openLostClients() {
    console.log(DASH_LOG_NS, "OPEN LOST CLIENTS → IDs:", this.state.kpis.lost_client_ids);

    if (!this.state.kpis.lost_client_ids || this.state.kpis.lost_client_ids.length === 0) {
      window.alert("No lost clients for this selection.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "res.partner",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", this.state.kpis.lost_client_ids]],
      name: "Lost Clients",
    });
  }

  openLostBrands() {
    console.log(DASH_LOG_NS, "OPEN LOST BRANDS → IDs:", this.state.kpis.lost_brand_ids);

    if (!this.state.kpis.lost_brand_ids.length) {
      this.env.services.notification.add("No Lost Brands found.", { type: "warning" });
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      name: "Lost Brands",
      res_model: "res.partner",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      view_mode: "list,form",
      domain: [["id", "in", this.state.kpis.lost_brand_ids]],
    });
  }

  openTopClient(ev) {
    const partnerId = Number(ev.currentTarget.dataset.id);
    const row = this.state.kpis.top_clients.find((x) => x.id === partnerId);

    if (!row) {
      console.error(DASH_LOG_NS, "No row found for partner:", partnerId);
      return;
    }

    const ids = row.invoice_ids || [];

    console.log(DASH_LOG_NS, "TOP CLIENT CLICKED → Partner:", row.name);
    console.log(DASH_LOG_NS, "Invoice IDs:", ids);
    console.log(DASH_LOG_NS, "Count:", ids.length);

    if (!ids.length) {
      window.alert("No invoices found for this client in selected range.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      name: "Invoices - " + row.name,
      res_model: "account.move",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", ids]],
    });
  }

  openTopBuyer(ev) {
    const buyerId = Number(ev.currentTarget.dataset.id);
    const row = this.state.kpis.top_buyers.find((x) => x.id === buyerId);

    if (!row) {
      console.error(DASH_LOG_NS, "No row found for buyer:", buyerId);
      return;
    }

    const ids = row.invoice_ids || [];

    console.log(DASH_LOG_NS, "TOP BUYER CLICKED → Buyer:", row.name);
    console.log(DASH_LOG_NS, "Invoice IDs:", ids);
    console.log(DASH_LOG_NS, "Count:", ids.length);

    if (!ids.length) {
      window.alert("No invoices found for this buyer in selected range.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      name: "Invoices - " + row.name,
      res_model: "account.move",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", ids]],
    });
  }

  async openTotalInvoices() {
    console.log(DASH_LOG_NS, "TOTAL INVOICES IDS:", this.state.kpis.total_invoices_ids);

    const ids = this.state.kpis.total_invoices_ids || [];
    if (!ids.length) {
      window.alert("No invoices found.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "account.move",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", ids]],
      name: "Total Invoices",
    });
  }

  async openPaidInvoices() {
    console.log(DASH_LOG_NS, "PAID INVOICE IDS:", this.state.kpis.paid_invoice_ids);

    const ids = this.state.kpis.paid_invoice_ids || [];
    if (!ids.length) {
      window.alert("No paid invoices found.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "account.move",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", ids]],
      name: "Paid Invoices",
    });
  }

  async openNotPaidInvoices() {
    console.log(DASH_LOG_NS, "NOT PAID INVOICE IDS:", this.state.kpis.not_paid_invoice_ids);

    const ids = this.state.kpis.not_paid_invoice_ids || [];
    if (!ids.length) {
      window.alert("No unpaid invoices found.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "account.move",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", ids]],
      name: "Unpaid (Not Paid) Invoices",
    });
  }

  async openPartialInvoices() {
    console.log(DASH_LOG_NS, "PARTIAL INVOICE IDS:", this.state.kpis.partial_invoice_ids);

    const ids = this.state.kpis.partial_invoice_ids || [];
    if (!ids.length) {
      window.alert("No partially paid invoices found.");
      return;
    }

    this.env.services.action.doAction({
      type: "ir.actions.act_window",
      res_model: "account.move",
      view_mode: "list,form",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: [["id", "in", ids]],
      name: "Partially Paid Invoices",
    });
  }
}

registry.category("actions").add("tti_dashboard_action", TTIDashboard);
export default TTIDashboard;
