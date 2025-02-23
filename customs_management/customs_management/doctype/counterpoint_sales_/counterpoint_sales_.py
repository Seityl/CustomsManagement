# Copyright (c) 2024, Sudeep Kulkarni and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CounterPointSales_(Document):
    # pass
	def validate(self):
		print("onssave")
		if frappe.db.exists("Counter Point Sales Log",self.name) and self.sales_invoice_created == 1:
			doc=frappe.get_doc("Counter Point Sales Log",self.name)
			doc.delete()
			print("doc deleted = ",self.name)
			
