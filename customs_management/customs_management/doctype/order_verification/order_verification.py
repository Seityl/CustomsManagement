# Copyright (c) 2025, Jollys Pharmacy Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class OrderVerification(Document):
    def on_submit(self):
        self.update_status('Verified')

    def update_status(self, status:str):
        self.db_set('status', status)

    @frappe.whitelist()
    def update_item_tariff_numbers(self):
        for item in self.items:
            current_tariff = frappe.db.get_value('Item', {'name': item.item}, ['customs_tariff_number'])
            
            if item.customs_tariff_number != current_tariff:
                if not frappe.db.exists('Customs Tariff Number', item.customs_tariff_number):
                    html_msg = (
                        '<div class="alert alert-danger">'
                        f"Customs Tariff Number does not exist:<br><br>{item.customs_tariff_number}<br><br>"
                        "Please add it using the dialog!"
                        "</div>"
                    )
                    return {'status': 'error', 'message': html_msg, 'customs_tariff_number': item.customs_tariff_number}

                frappe.db.savepoint('sp')

                try:
                    frappe.db.set_value('Item', item.item, 'customs_tariff_number', item.customs_tariff_number)
                    frappe.db.set_value('Invoice Verification Item', item.name, 'customs_tariff_number', item.customs_tariff_number)
                    frappe.db.commit()

                except Exception as e:
                    frappe.db.rollback()
                    frappe.log_error(frappe.get_traceback(), _("update_item_tariff_numbers"))
                    frappe.throw(str(e))

        return {'status': 'success'}

    @frappe.whitelist()
    def create_tariff_number(self, values):
        tariff_number = frappe.new_doc('Customs Tariff Number')
        tariff_number.update({
            'tariff_number': values['tariff_number'],
            'description': values['description'],
            'custom_precision': values['custom_precision'],
            'custom_markup_percentage': values['custom_markup_percentage'],
            'custom_surcharge_percentage': values['custom_surcharge_percentage'],
            'custom_duty_percentage': values['custom_duty_percentage'],
            'custom_vat_percentage': values['custom_vat_percentage'],
            'custom_service_charge_percentage': values['custom_service_charge_percentage'],
            'custom_excise_percentage': values['custom_excise_percentage']
        })

        frappe.db.savepoint('sp')

        try:
            tariff_number.insert()
            frappe.db.commit()

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), _("create_tariff_number"))
            frappe.throw(_("Error in create_tariff_number: {0}").format(str(e)))

        html_msg = (
            '<div class="alert alert-success">'
            f"Customs Tariff Number added successully:<br><br>{values['tariff_number']}<br><br>"
            "</div>"
        )
        return {'status': 'success', 'message': html_msg}
