// D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_sales_dash\static\src\js\tti_dashboard.js

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";
import { onPatched } from "@odoo/owl";


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
    className: { type: String, optional: true },
  };

  setup() {
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
      category: [],
      subcategory: [],
      zone: [],
      kpis: {
        total_sales: 0,
        total_recovery: 0,
        recovered_pct: 0,

        pending_so: 0,
        open_quotations: 0,
        mom_growth: 0,
        pop_growth: 0,
        yoy_growth: 0,
        samples_run: 0,
        pending_reports: 0,
        reports_sent: 0,
        top_clients: [],
        total_invoices: 0,
        paid_invoices: 0,
        not_paid_invoices: 0,
        partial_invoices: 0,
        top_buyers: [],
        new_clients: 0,
        new_brands: 0,
        lost_clients: 0,
        lost_brands: 0,
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
      await this.loadFilters();

      // Don’t auto-fetch on mount; keep blank until all 4 selectors are set
      this.blankKPIsAndCharts();

      try {
        await loadJS("/web/static/lib/Chart/Chart.js");
      } catch (e) {
        console.warn("Chart.js failed to load", e);
      }
      // Initial render (blank)
      this.renderPartnerPie();
      this.renderSalesLine();
      this.renderDivisionBar();
      this.attachMultiNoCtrl();
    });

    onPatched(() => {
  this.attachMultiNoCtrl();
});


  }



  // ---------- small helpers ----------
  isEmptySel(v) {
    return v === "none" || v === "null" || v === null || v === undefined || v === "";
  }

  anyMissingRange() {
    return (
      this.isEmptySel(this.state.from_period) ||
      this.isEmptySel(this.state.to_period) ||
      this.isEmptySel(this.state.from_year) ||
      this.isEmptySel(this.state.to_year)
    );
  }

  blankKPIsAndCharts() {
    Object.assign(this.state.kpis, {
      total_sales: 0,
      total_recovery: 0,
      recovered_pct: 0,
      pending_so: 0,
      open_quotations: 0,
      mom_growth: 0,
      pop_growth: 0,
      yoy_growth: 0,
      samples_run: 0,
      pending_reports: 0,
      reports_sent: 0,
      top_clients: [],
      total_invoices: 0,
      paid_invoices: 0,
      not_paid_invoices: 0,
      partial_invoices: 0,
      top_buyers: [],
      new_clients: 0,
      new_brands: 0,
      lost_clients: 0,
      lost_brands: 0,
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
  const f = await rpc("/tti_sales_dashboard/filters", {});
  this.state.periods = f.periods || [];
  this.state.years = f.years || [];
  this.state.categories = f.categories || [];
  this.state.subcategories = f.subcategories || [];
  this.state.zones = f.zones || [];

  // set defaults from backend
  this.state.from_period = f.default_from_period;
  this.state.to_period   = f.default_to_period;
  this.state.from_year   = f.default_from_year;
  this.state.to_year     = f.default_to_year;

  // immediately load KPIs for current month/year
  await this.fetchData();
}


  async onFilterChange(ev) {
  const el = ev.target;

  // Handle multi-selects (category, subcategory, zone)
if (el && el.multiple) {
  const selected = Array.from(el.selectedOptions)
    .map(opt => opt.value)
    .filter(v => v !== "");

  if (el.name === "category") {
    this.state.category = selected;
  } else if (el.name === "subcategory") {
    this.state.subcategory = selected;
  } else if (el.name === "zone") {
    this.state.zone = selected;
  }
}


  // Validation for period/year filters
  if (this.anyMissingRange()) {
    this.blankKPIsAndCharts();
    return;
  }

  const fp = Number(this.state.from_period);
  const tp = Number(this.state.to_period);
  const fy = Number(this.state.from_year);
  const ty = Number(this.state.to_year);

  if (fy > ty || (fy === ty && fp > tp)) {
    window.alert("Invalid period range.\nFrom date is after To date.\nPlease correct Months/Years.");
    return;
  }

  await this.fetchData();
}


  // -----------------------
  // Charts
  // -----------------------
  renderPartnerPie() {
    const el = document.getElementById("partner_pie_chart");
    const data = this.state.kpis.partner_pie || [];
    if (!el || !window.Chart) return;

    if (this._partnerChart) {
      this._partnerChart.destroy();
      this._partnerChart = null;
    }

    this._partnerChart = new Chart(el, {
      type: "pie",
      data: {
        labels: data.map((d) => d.label),
        datasets: [
          {
            data: data.map((d) => d.value),
            backgroundColor: ["#4e79a7", "#f28e2b", "#e15759"],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.label}: ${ctx.parsed}%`,
            },
          },
        },
      },
    });
  }

  renderSalesLine() {
    const el = document.getElementById("sales_line_chart");
    const data = this.state.kpis.sales_line || { labels: [], series: [] };
    if (!el || !window.Chart) return;

    if (this._salesChart) {
      this._salesChart.destroy();
      this._salesChart = null;
    }

    this._salesChart = new Chart(el, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: data.series.map((s) => ({
          label: s.label,
          data: s.data.map((v) => v / 1_000_000), // convert to millions
          fill: false,
          tension: 0.3,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
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
    if (!el || !window.Chart) return;

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
        plugins: { legend: { display: false } },
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
    // Extra safety: stop here if somehow called with missing range
    if (this.anyMissingRange()) {
      this.blankKPIsAndCharts();
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

    if (fy > ty || (fy === ty && fp > tp)) {
      window.alert("Invalid period range.\nFrom date is after To date.\nPlease correct Months/Years.");
      return;
    }

    // ✅ Send ONLY the filters — no nested objects
    const payload = {
      from_period: fp,
      to_period: tp,
      from_year: fy,
      to_year: ty,
      category: Array.isArray(this.state.category) ? this.state.category : [],
      subcategory: Array.isArray(this.state.subcategory) ? this.state.subcategory : [],
      zone: Array.isArray(this.state.zone) ? this.state.zone : [],
    };

    console.debug("[TTI DASH] Sending payload to server:", payload);

    let res;
    try {
      res = await rpc("/tti_sales_dashboard/filter_data", { data: payload });
    } catch (e) {
      // 👇 Surface the real server error from Odoo
      console.error("Dashboard RPC failed:", e);
      const serverMsg =
        (e && e.message) ||
        (e && e.data && e.data.message) ||
        (e && e.data && e.data.debug) ||
        (e && e.data && e.data.name) ||
        "Unknown server error";
      window.alert("Server error:\n" + serverMsg);
      return;
    }

    Object.assign(this.state.kpis, {
      total_sales: res.total_sales ?? 0,
      total_recovery: res.total_recovery ?? 0,
      recovered_pct: res.recovered_pct ?? 0,
      pending_so: res.pending_so ?? 0,
      open_quotations: res.open_quotations ?? 0,
      mom_growth: res.mom_growth ?? 0,
      pop_growth: res.pop_growth ?? 0,
      yoy_growth: res.yoy_growth ?? 0,
      samples_run: res.samples_run ?? 0,
      pending_reports: res.pending_reports ?? 0,
      reports_sent: res.reports_sent ?? 0,
      top_clients: Array.isArray(res.top_clients) ? res.top_clients : [],
      total_invoices: res.total_invoices ?? 0,
      paid_invoices: res.paid_invoices ?? 0,
      not_paid_invoices: res.not_paid_invoices ?? 0,
      partial_invoices: res.partial_invoices ?? 0,
      top_buyers: Array.isArray(res.top_buyers) ? res.top_buyers : [],
      new_clients: res.new_clients ?? 0,
      new_brands: res.new_brands ?? 0,
      lost_clients: res.lost_clients ?? 0,
      lost_brands: res.lost_brands ?? 0,
      partner_pie: Array.isArray(res.partner_pie) ? res.partner_pie : [],
      sales_line: res.sales_line ?? { labels: [], series: [] },
      division_bar: res.division_bar ?? { labels: [], series: [] },
      targets_achieved: Array.isArray(res.targets_achieved) ? res.targets_achieved : [],
      targets_total_pct: res.targets_total_pct ?? 0,
      targets_filters_applied: res.targets_filters_applied ?? false,
    });

    if (typeof window.Chart !== "undefined") {
      this.renderPartnerPie();
      this.renderSalesLine();
      this.renderDivisionBar();
    }
  }

  initMultiSelects() {
  const selects = document.querySelectorAll('select.ts-multi');
  selects.forEach((sel) => {
    // Destroy previous instance if any (when re-rendered)
    if (sel._tom) {
      sel._tom.destroy();
      sel._tom = null;
    }
    // Create Tom Select instance
    sel._tom = new window.TomSelect(sel, {
      plugins: ['remove_button'],
      persist: false,
      create: false,
      allowEmptyOption: true,
      hideSelected: true,
      maxOptions: 10000,
      placeholder: 'All',
      onChange: () => {
        // Fire a normal change event so Owl handler runs
        sel.dispatchEvent(new Event('change', { bubbles: true }));
      },
      render: {
        no_results: function(data, escape) {
          return `<div class="no-results">No results for "${escape(data.input)}"</div>`;
        },
      },
    });
  });
}

attachMultiNoCtrl() {
  // Make all <select multiple> behave like checkbox lists (no Ctrl needed)
  const selects = document.querySelectorAll('select[multiple]');
  selects.forEach((sel) => {
    // avoid duplicate handlers on re-render
    if (sel._hasNoCtrl) return;
    sel._hasNoCtrl = true;

    sel.addEventListener('mousedown', (e) => {
      const target = e.target;
      if (target && target.tagName === 'OPTION') {
        e.preventDefault();            // stop native selection behavior
        target.selected = !target.selected;  // toggle like a checkbox
        // ensure the <select> fires a change event for Owl
        sel.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });
}


}

registry.category("actions").add("tti_dashboard_action", TTIDashboard);
export default TTIDashboard;
