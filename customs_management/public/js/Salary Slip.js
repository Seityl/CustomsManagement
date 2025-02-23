frappe.ui.form.on('Salary Slip', {
    // refresh:function(frm){
    //     console.log("Salalry Slip refresh")
    // },
    // date:async function(frm){
    //     console.log("date",frm.doc.date) 
    //     frappe.call({
    //         method : 'customs_management.api.check_holiday',
    //         freeze:true,
    //         freeze_message:"Checking holiday list",
    //         args: {
    //             date:frm.doc.date,
                
    //         },
    //         async:false,
    //         callback:function(resp){
    //             console.log(resp)
    //             if (resp.message){
    //                 frm.doc.custom_ot_multiplier_type="Holiday OT Multiplier"
    //                 frm.refresh_field("custom_ot_multiplier_type")
    //             }else{
    //                 frm.doc.custom_ot_multiplier_type="Regular Multiplier"
    //                 frm.refresh_field("custom_ot_multiplier_type")
    //             }
    //         }
    //     })

    // },
})