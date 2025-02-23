from frappe import _


def get_data():
	
	return {
		"fieldname": "customs_entry",
		"non_standard_fieldnames": {
		},
		"internal_links": {
			"Purchase Invoice": ["items", "reference_document"],
			"Purchase Receipt": ["items", "reference_document"],
		},
		"transactions": [
			{
				"label": _("Reference"),
				"items": ["Landed Cost Voucher"],
			},
		],
	}
