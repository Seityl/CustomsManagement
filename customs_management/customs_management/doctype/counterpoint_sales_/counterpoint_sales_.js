// Copyright (c) 2024, Sudeep Kulkarni and contributors
// For license information, please see license.txt

frappe.ui.form.on('CounterPoint Sales_', {
	refresh: function(frm) {
		frm.add_custom_button(__('Create Sales Invoice'), function() {

						frappe.call({
							method : "create_sales_invoice",
							doc : frm.doc,
							args:{
								
							},
							freeze:true,
							freeze_message:"Creating Sales Invoice",
							callback:function(r){

							}
						})
						
					
				
			
			console.log("purchase receipt")
		});
	}
});
