# Copyright (c) 2023, Sudeep Kulkarni and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ItemPriceRevision(Document):
	@frappe.whitelist()
	def get_markup_summary(self):
		if self.shipment_clearing:
			doc = frappe.get_doc('Shipment Clearing', self.shipment_clearing)
			print("SC DOC ==============", doc)	
			self.markup_summary = doc.markup_summary