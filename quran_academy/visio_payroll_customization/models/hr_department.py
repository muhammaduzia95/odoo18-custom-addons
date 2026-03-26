from odoo import api, fields, models

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    department_sequence = fields.Char(string="Department Code", readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        # Generate the department sequence during creation
        department = super(HrDepartment, self).create(vals_list)
        department._compute_full_sequence()
        return department

    def write(self, vals):
        # Override write to handle updates to parent_id
        result = super(HrDepartment, self).write(vals)
        if 'parent_id' in vals:
            self._compute_full_sequence()
        return result

    def _compute_full_sequence(self):
        for department in self:
            # Step 1: Build the full parent hierarchy sequence
            parent_sequence_parts = []  # Initialize an empty list to hold parent numeric parts
            parent = department.parent_id
            while parent:
                if parent.department_sequence:
                    # Extract the numeric part from the parent's sequence and add it to the start of the list
                    parent_sequence_parts.insert(0, parent.department_sequence.split('/')[-1])
                # Move to the next parent in the hierarchy
                parent = parent.parent_id

            # Step 2: Generate or retain the department's own number
            if department.department_sequence:
                # If the department already has a sequence, split it into parts
                current_parts = department.department_sequence.split('/')
            else:
                # If no sequence exists, initialize as an empty list
                current_parts = []

            if len(current_parts) > 1 and current_parts[-1].isdigit() and current_parts[0] == "DEP":
                # If the sequence starts with "DEP" and ends with a number, retain the existing number
                own_number = current_parts[-1]
            else:
                # Otherwise, generate a new unique number for the department
                own_number = self.env['ir.sequence'].next_by_code('hr.department.number').replace('DEP', '')

            # Step 3: Construct the full sequence
            parent_sequence = '/'.join(parent_sequence_parts)  # Join parent parts with '/'
            if parent_sequence:
                # If there is a parent sequence, include it in the full sequence
                department.department_sequence = f"DEP/{parent_sequence}/{own_number}"
            else:
                # If no parent sequence, use only the department's own number
                department.department_sequence = f"DEP/{own_number}"

            # Step 4: Update child departments recursively
            children = self.search([('parent_id', '=', department.id)])  # Find all child departments
            for child in children:
                child._compute_full_sequence()  # Recursively update the sequence for each child
