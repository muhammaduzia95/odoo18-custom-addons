/** @odoo-module **/

import {Component, onMounted, useEffect, useRef, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";

import {SectionAndNoteText} from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks"


patch(SectionAndNoteText.prototype, {
    setup() {
        this.copyElement = useRef("copyElement");
        this.orm = useService("orm")
        this.action = useService("action");
        this.notification = useService("notification");
        onMounted(() => {
            if (this.props.record.data.display_type == 'line_section' && this.props.record.model.config.resModel == 'sale.order') {
                this.copyElement.el.style.display = 'block';
            } else {
                this.copyElement.el.style.display = 'none';
            }
        });
    },
    async copyLines() {

        var confirm = window.confirm("Are you sure to copy this section?");
        var order_id = this.props.record.model.config.resId
        var line_id = this.props.record.evalContext.active_id
        if (confirm) {
            const res = await this.orm.call('sale.order', 'copy_section_with_products', [], {
                order_id: order_id,
                line_id: line_id
            });
            if (res) {
                this.notification.add(_t("Section copied successfully"), {type: 'success'});

            }
            return this.action.doAction(
                {
                    type: "ir.actions.act_window",
                    res_model: "sale.order",
                    res_id: order_id,
                    views: [[false, "form"]],
                    target: "current",
                },
                {clearBreadcrumbs: false}
            );
        }

        // await this.orm.call('sale.order', 'test', [], {});
    }
});

