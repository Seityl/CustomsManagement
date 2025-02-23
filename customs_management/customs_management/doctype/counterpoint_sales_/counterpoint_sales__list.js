frappe.listview_settings['CounterPoint Sales_'] = {
    refresh: function(listview) {
        listview.page.add_inner_button("Create Sales Invoice", function() {
            frappe.call({
                method : "customs_management.api.create_sales_invoice",
                args:{
                   
                },
                freeze:true,
                freeze_message:"Creating Sales Invoice",
                callback:function(r){
                    console.log(r)
                }
            })
            
            console.log("purchase receipt")
        });

        listview.page.add_inner_button("Reset", function() {
            frappe.call({
                method : "customs_management.api.reset",
                args:{
                   
                },
                freeze:true,
                freeze_message:"reset",
                callback:function(r){
                    console.log(r)
                }
            })
            
            console.log("purchase receipt")
        });

    },
 };