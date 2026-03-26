/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class PayslipDashboard extends Component {
    static template = "visio_payroll_customization.PayslipDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");

        onWillStart(async () => {
            this.payslipData = await this.orm.call("hr.payslip", "retrieve_dashboard");
        });
    }

    async openWizard(ev) {
        const wizardRef = ev.currentTarget.getAttribute("wizard_ref");
        const buttonText = ev.currentTarget.textContent.trim();

        if (wizardRef) {
            // Define confirmation messages based on the wizard reference or button text
            let confirmationMessage = "";
            let confirmationTitle = "";
            let confirmClass = "btn-primary"; // Default confirm button color
            let cancelClass = "btn-secondary"; // Default cancel button color
            let confirmLabel = "Yes, Proceed";
            let cancelLabel = "Cancel";

            switch (wizardRef) {
                case "visio_payroll_customization.action_duplicate_payslips_wizard":
                    confirmationTitle = "Generate Payslips Confirmation";
                    confirmationMessage = "Warning - Are you sure you want to generate payslips? This can't be undone.";
                    confirmClass = "btn-info";     // Light blue for generate
                    confirmLabel = "Generate";
                    break;
                case "visio_payroll_customization.action_import_excel":
                    confirmationTitle = "Update Payslips Confirmation";
                    confirmationMessage = "Warning - Are you sure you want to update payslips? This can't be undone.";
                    confirmClass = "btn-primary";  // Blue for update
                    confirmLabel = "Update";
                    break;
                case "visio_payroll_customization.action_post_payslips_wizard":
                    confirmationTitle = "Post Payslips";
                    confirmationMessage = "Warning - Are you sure you want to post all draft payslips? This can't be undone.";
                    confirmClass = "btn-success";  // Green for post
                    confirmLabel = "Post";
                    break;
                default:
                    confirmationTitle = "Confirm Action";
                    confirmationMessage = `Are you sure you want to proceed with ${buttonText}?`;
                    confirmClass = "btn-warning"; // Orange for unknown actions
            }

            // Show confirmation dialog
            this.dialog.add(ConfirmationDialog, {
                title: confirmationTitle,
                body: confirmationMessage,
                confirmLabel: "Okay", // Custom confirm button text
                cancelLabel: "Cancel",        // Custom cancel button text
                confirmClass: "btn-danger",  // Bootstrap class for confirm button
                confirm: () => {
                    this.action.doAction(wizardRef);
                },
                cancel: () => {
                    // Optional: Add any cleanup logic here if needed
                    console.log("Action cancelled by user");
                }
            });
        }
    }
}