frappe.ui.form.on('Customs Tariff Number',{
    refresh	: function(frm) {
        frm.set_query("custom_duty_account", function(){
            return {
                "filters": [
                    ["Account", "account_type", "=", "Expense Account"],
                    ["Account", "account_type", "=", "Expenses Included In Valuation"]
                ]
            }
        });
        frm.set_query("custom_vat_account", function(){
            return {
                "filters": [
                    ["Account", "account_type", "=", "Expense Account"],
                    ["Account", "account_type", "=", "Expenses Included In Valuation"]
                ]
            }
        });
        frm.set_query("custom_service_charge_account", function(){
            return {
                "filters": [
                    ["Account", "account_type", "=", "Expense Account"],
                    ["Account", "account_type", "=", "Expenses Included In Valuation"]
                ]
            }
        });
        frm.set_query("custom_surcharge_account", function(){
            return {
                "filters": [
                    ["Account", "account_type", "=", "Expense Account"],
                    ["Account", "account_type", "=", "Expenses Included In Valuation"]
                ]
            }
        });
        frm.set_query("custom_markup_account", function(){
            return {
                "filters": [
                    ["Account", "account_type", "=", "Expense Account"],
                    ["Account", "account_type", "=", "Expenses Included In Valuation"]
                ]
            }
        });
        frm.set_query("custom_excise_account", function(){
            return {
                "filters": [
                    ["Account", "account_type", "=", "Expense Account"],
                    ["Account", "account_type", "=", "Expenses Included In Valuation"]
                ]
            }
        });
    }
})