from odoo import api, models



class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_quotation_send(self):
        action = super().action_quotation_send()

        template = self.env['mail.template'].search([
            ('name', '=', 'Freight Quotation for Order - CIT')
        ], limit=1)

        print("\n=== DEBUG: START action_quotation_send ===")
        print("SO ids:", self.ids)
        print("SO name(s):", [so.name for so in self])
        print("Template FOUND?:", bool(template))
        if template:
            print("Template ID/Name:", template.id, "/", template.name)
        else:
            print("Template not found; returning original action")
            print("=== DEBUG: END action_quotation_send ===\n")
            return action

        # Collect SO attachments
        so_attach_ids = self.document_attachment_so.ids
        so_attach_names = [a.name for a in self.document_attachment_so]
        print("SO document_attachment_so COUNT:", len(so_attach_ids))

        # Smart sample: print only items #5 and #6 (1-based); else print all if < 6
        if len(so_attach_names) >= 6:
            print("Sample attachments [#5, #6]:")
            # indices 4 and 5 are 5th and 6th (0-based)
            print("  #5:", so_attach_names[4] if len(so_attach_names) > 4 else "N/A")
            print("  #6:", so_attach_names[5] if len(so_attach_names) > 5 else "N/A")
        else:
            print("All attachment names (since < 6):", so_attach_names)

        # Pass guards + raw ids so the wizard can add/remove on template change
        ctx = dict(action.get('context', {}))
        ctx.update({
            'default_use_template': True,
            # We do NOT force-select our template; user may start on another then switch
            # If you want to open already on this template, uncomment the next line:
            # 'default_template_id': template.id,

            'so_auto_attach_template_id': template.id,
            'so_auto_attach_ids': so_attach_ids,
        })
        action['context'] = ctx

        print("Context keys set:",
              "so_auto_attach_template_id" in ctx,
              "so_auto_attach_ids" in ctx)
        print("=== DEBUG: END action_quotation_send ===\n")
        return action


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.onchange('template_id')
    def _onchange_template_id_autoload_so_attachments(self):
        """When user switches template:
           - If it becomes the allowed template => add missing SO files
           - If it becomes something else       => remove only those SO files (keep user-added)
        """
        allowed_id = self._context.get('so_auto_attach_template_id')
        so_attach_ids = self._context.get('so_auto_attach_ids') or []

        print("\n=== DEBUG: onchange(template_id) ===")
        print("Allowed tmpl id:", allowed_id)
        print("Chosen tmpl id:", self.template_id.id if self.template_id else None)
        print("SO attach ids COUNT:", len(so_attach_ids))

        # Smart sample output for SO files list
        if len(so_attach_ids) >= 6:
            print("SO attach ids sample [#5, #6]:",
                  (so_attach_ids[4] if len(so_attach_ids) > 4 else None),
                  (so_attach_ids[5] if len(so_attach_ids) > 5 else None))
        else:
            print("SO attach ids (since < 6):", so_attach_ids)

        if not allowed_id:
            print("No allowed template in context; doing nothing.")
            print("=== DEBUG: onchange END ===\n")
            return

        existing_ids = set(self.attachment_ids.ids)
        print("Current wizard attachment COUNT:", len(existing_ids))

        if self.template_id and self.template_id.id == allowed_id:
            # Add missing SO attachments
            to_add = [att for att in so_attach_ids if att not in existing_ids]
            print("Will ADD COUNT:", len(to_add))
            if len(to_add) >= 6:
                print("ADD sample [#5, #6]:",
                      (to_add[4] if len(to_add) > 4 else None),
                      (to_add[5] if len(to_add) > 5 else None))
            else:
                print("ADD all (since < 6):", to_add)
            if to_add:
                self.attachment_ids = [(4, att) for att in to_add]
        else:
            # Remove only the SO-provided attachments to avoid leakage
            to_remove = [att for att in self.attachment_ids.ids if att in so_attach_ids]
            print("Will REMOVE COUNT:", len(to_remove))
            if len(to_remove) >= 6:
                print("REMOVE sample [#5, #6]:",
                      (to_remove[4] if len(to_remove) > 4 else None),
                      (to_remove[5] if len(to_remove) > 5 else None))
            else:
                print("REMOVE all (since < 6):", to_remove)
            if to_remove:
                self.attachment_ids = [(3, att) for att in to_remove]

        print("Final wizard attachment COUNT:", len(self.attachment_ids.ids))
        print("=== DEBUG: onchange END ===\n")

    def send_mail(self, auto_commit=False):
        """Safety net at send-time: ensure files are present if the allowed template is selected."""
        allowed_id = self._context.get('so_auto_attach_template_id')
        so_attach_ids = self._context.get('so_auto_attach_ids') or []

        print("\n=== DEBUG: send_mail() ===")
        print("Allowed tmpl id:", allowed_id)
        print("Chosen tmpl id:", self.template_id.id if self.template_id else None)
        print("SO attach ids COUNT:", len(so_attach_ids))

        if allowed_id and self.template_id and self.template_id.id == allowed_id and so_attach_ids:
            existing = set(self.attachment_ids.ids)
            to_add = [att for att in so_attach_ids if att not in existing]
            print("Send-time ensure ADD COUNT:", len(to_add))
            if len(to_add) >= 6:
                print("Send-time ADD sample [#5, #6]:",
                      (to_add[4] if len(to_add) > 4 else None),
                      (to_add[5] if len(to_add) > 5 else None))
            else:
                print("Send-time ADD all (since < 6):", to_add)
            if to_add:
                self.attachment_ids = [(4, att) for att in to_add]
        else:
            print("No send-time auto-attach (template mismatch or empty list).")

        print("Final wizard attachment COUNT (before super):", len(self.attachment_ids.ids))
        print("=== DEBUG: send_mail END ===\n")
        return super().send_mail(auto_commit=auto_commit)
