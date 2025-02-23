// Copyright (c) 2023, Sudeep Kulkarni and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Price Revision', {
	get_markup_summary : function(frm){
		frappe.call({
			method : 'get_markup_summary',
			doc : frm.doc,
			callback:function(res){
				console.log(res)
				frm.refresh_field('markup_summary');
			}
		});
	}
});
