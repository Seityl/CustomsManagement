from frappe import _

def get_data():
	return {
		'fieldname': 'customs_entry',
		'internal_links': {
			'Purchase Receipt': ['items', 'reference_document'],
		},
		'transactions': [
			{
				'label': _('Reference'),
				'items': [
					'Landed Cost Voucher',
			        'Purchase Receipt'
				]
			}
		]
	}
