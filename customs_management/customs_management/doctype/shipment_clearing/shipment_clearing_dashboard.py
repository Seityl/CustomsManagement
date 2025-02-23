from frappe import _


def get_data():
	return {
		"fieldname": "customs_entry",
		"non_standard_fieldnames": {
		},
		"internal_links": {
		},
		"transactions": [
			{
				"label": _("Reference"),
				"items" : ["Price Revision"]
			},
		],
	}
