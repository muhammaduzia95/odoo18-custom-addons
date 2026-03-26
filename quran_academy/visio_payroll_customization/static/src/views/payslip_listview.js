/** @odoo-module **/
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { PayslipDashboard } from "@visio_payroll_customization/views/payslip_dashboard";

export class PayslipListRenderer extends ListRenderer {
    static template = "visio_payroll_customization.PayslipListView";
    static components = Object.assign({}, ListRenderer.components, { PayslipDashboard });
}

export const PayslipListView = {
    ...listView,
    Renderer: PayslipListRenderer,
};

registry.category("views").add("payslip_dashboard", PayslipListView);
