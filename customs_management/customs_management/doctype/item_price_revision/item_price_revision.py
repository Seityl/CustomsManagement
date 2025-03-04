# Copyright (c) 2023, Sudeep Kulkarni and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ItemPriceRevision(Document):
	@frappe.whitelist()
	def get_markup_summary(self):
		if self.costing:
			doc = frappe.get_doc('Costing', self.costing)
			print("SC DOC ==============", doc)	
			self.markup_summary = doc.markup_summary