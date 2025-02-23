frappe.ui.form.on('Sales Invoice', {
    refresh:function(frm){
        console.log("sales invoice")
        if (frm.doc.docstatus == 1){
          if (frm.doc.custom_export){
            frm.trigger('add_download')

          }else{
            frm.remove_custom_button('Download XML');
          }
        }
    },

    custom_export :function(frm){
      if (frm.doc.custom_export){
        frm.trigger("add_download")
      }else{
        frm.remove_custom_button('Download XML');
      }
    },

    add_download: function(frm){
      frm.add_custom_button(('Download XML'), function() {

        var w = window.open(
            frappe.urllib.get_full_url(
              "/api/method/customs_management.sales_xml.sales_xml?"+
                "name=" +
                encodeURIComponent(frm.doc.name)
            )
          );
          if (!w) {
            frappe.msgprint(__("Please enable pop-ups"));
            return;
          }
        // frappe.call({
        //     method : "customs_management.sales_xml.sales_xml",
        //     args:{
        //        name:frm.doc.name
        //     },
        //     freeze:true,
        //     freeze_message:"Generating XML",
        //     callback:function(r){
        //         console.log(r)
        //     }
        // })
      })

    }
})