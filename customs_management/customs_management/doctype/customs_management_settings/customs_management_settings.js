// Copyright (c) 2023, Sudeep Kulkarni and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customs Management Settings', {
	refresh: function(frm) {
		frm.set_query("bank_expense_account", function(){
            return {
                "filters": [
                    ["Account", "account_type",'in', ['Tax','Chargeable', 'Income Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation']],
					['company','=', "Jollys Pharmacy Limited"]
                ]
            }
        });
		frm.set_query("handler_expense_account", function(){
            return {
                "filters": [
                    ["Account", "account_type",'in', ['Tax','Chargeable', 'Income Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation']],
					['company','=', "Jollys Pharmacy Limited"]
                ]
            }
        });
		frm.fields_dict['tariff_accounts'].grid.get_field('duty_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Cost of Goods Sold','Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}

		frm.fields_dict['tariff_accounts'].grid.get_field('vat_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}
		frm.fields_dict['tariff_accounts'].grid.get_field('service_charge_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}
		frm.fields_dict['tariff_accounts'].grid.get_field('surcharge_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}
		frm.fields_dict['tariff_accounts'].grid.get_field('excise_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}
		frm.fields_dict['tariff_accounts'].grid.get_field('handler_expense_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Cost of Goods Sold', 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}
		frm.fields_dict['tariff_accounts'].grid.get_field('bank_expense_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Cost of Goods Sold', 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}
		// tariff account child end

		frm.fields_dict['tariff_management_additional_charges'].grid.get_field('expense_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}
		frm.fields_dict['shipment_clearing_additional_charges'].grid.get_field('expense_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company],
					['is_group','=','0']
				]
			}
		}
		frm.fields_dict['customs_entry_additional_charges'].grid.get_field('expense_account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			// console.log(child);
			return {    
				filters:[
					['account_type', 'in', [ 'Chargeable', 'Expense Account','Expenses Included In Asset Valuation', 'Expenses Included In Valuation','Income Account', 'Tax']],
					['company','=', child.company]
				]
			}
		}

	}
});
frappe.ui.form.on('Custom Additional Charges', {
	expense_account:function(frm,cdt,cdn){
		let child=locals[cdt][cdn]
	
		frappe.call({
			method : 'get_exchange',
			doc : frm.doc,
			callback : function(resp){
				
				child.account_currency=resp.message[0]
				child.exchange_rate=resp.message[1]
				child.base_amount=resp.message[2]
				// frappe.model.set_value(cdt,cdn,'account_currency',resp.message[3])
				frm.refresh_field("additional_charges")
				
			}
		})
		// console.log(resp)
	
},

})
frappe.ui.form.on('Shipment Additional Charges',{
	expense_account:function(frm,cdt,cdn){
		let child=locals[cdt][cdn]
	
		frappe.call({
			method : 'get_exchange',
			doc : frm.doc,
			callback : function(resp){
				
				child.account_currency=resp.message[0]
				child.exchange_rate=resp.message[1]
				child.base_amount=resp.message[2]
				// frappe.model.set_value(cdt,cdn,'account_currency',resp.message[3])
				frm.refresh_field("additional_charges")
				
			}
		})
		// console.log(resp)
	
	},
})
frappe.ui.form.on('Tariff Additional Charges',{
	expense_account:function(frm,cdt,cdn){
		let child=locals[cdt][cdn]
	
		frappe.call({
			method : 'get_exchange',
			doc : frm.doc,
			callback : function(resp){
				console.log(resp)
				child.account_currency=resp.message[0]
				child.exchange_rate=resp.message[1]
				child.base_amount=resp.message[2]
				// frappe.model.set_value(cdt,cdn,'account_currency',resp.message[3])
				frm.refresh_field("additional_charges")
				
			}
		})
		
	
	},
	amount:function(frm,cdt,cdn){
		let child=locals[cdt][cdn]
	
		frappe.call({
			method : 'get_exchange',
			doc : frm.doc,
			callback : function(resp){
				console.log(resp)
				child.account_currency=resp.message[0]
				child.exchange_rate=resp.message[1]
				child.base_amount=resp.message[2]
				frm.refresh_field("additional_charges")
				
			}
		})
	}
})
