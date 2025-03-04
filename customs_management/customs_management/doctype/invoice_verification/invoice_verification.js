// Copyright (c) 2025, Jollys Pharmacy Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice Verification", {
    reference_doctype: function (frm) {
        var names = [];
        frappe.call({
          method: "get_tarif_application",
          doc: frm.doc,
          callback: function (lis) {
            names = lis.message;
            console.log("lissssssssssss", lis.message);
          },
        });
    
        if (frm.doc.company && frm.doc.reference_doctype == "Purchase Invoice") {
          frm.set_query("reference_document", () => {
            return {
              filters: [
                ["company", "=", frm.doc.company],
                ["docstatus", "=", 1],
                ["update_stock", "=", 1],
              ],
              fields: ["reference_document", "creation"],
              order_by: "creation desc",
            };
          });
        } else {
          frm.set_query("reference_document", () => {
            return {
              filters: [
                // ["name","in",names],
                ["company", "=", frm.doc.company],
                ["docstatus", "=", 1],
              ],
              fields: ["reference_document", "creation"],
              order_by: "creation desc",
            };
          });
          console.log("ppppppppppppppppp");
        }
      },
    
      reference_document: function (frm) {
        if (frm.doc.reference_document) {
          frappe.call({
            method: "get_items_by_purchase_invoice",
            doc: frm.doc,
            callback: function (resp) {
              frm.refresh_field("items");
              frm.refresh_field("tariff_number_summary");
              frm.refresh_field("grand_total");
              frm.refresh_field("total_item_qty");
              frm.refresh_field("item_count");
              frm.refresh_field("currency");
              frm.refresh_field("suppliers_name");
              console.log(resp);
            },
          });
        }
      },
      onload: function (frm) {
        console.log("ONload ");
        if (frm.doc.__islocal) {
          frappe.call({
            method: "get_default_additional_charges",
            doc: frm.doc,
            callback: function (resp) {
              frm.refresh_field("additional_charges");
            },
          });
        }
        // frappe.get_doc('Item',frm.doc.name).then(values => {
        // 		debugger
        // 		console.log(values);
        // 	})
      },
      refresh: function (frm) {
        if (!frm.doc.__islocal) {
          frm.add_custom_button(__("Go to Split up"), function () {
            console.log("go to summary");
            frappe.set_route(`app/print/Invoice Verification/${frm.doc.name}`);
          });
        }
        // frm.add_custom_button(__("Test"), function () {
        //   let base_amount = 0;
        //   let amount = 0;
        //   for (let i of frm.doc.items) {
        //     console.log("ref doc",i.reference_document)
        //     // if (i.reference_document != 'MAT-PRE-2024-00032'){
        //     //   continue
        //     // }
            //     console.log("i",i,i.amount,i.base_amount)
        //     base_amount += i.amount;
        //     amount += i.base_amount;
        //   }
        //   console.log("base_amount",base_amount)
        //   console.log("amount",amount)
        // });
    
        if (!frm.doc.__islocal && frm.doc.docstatus == 0){
          
          frm.add_custom_button(__("Update tariff number"), function () {
            console.log("Update tariff number");
            frappe.call({
            method: "update_tariff",
            doc: frm.doc,
            freeze:true,
            freeze_message:"updating tariff number",
            callback: function (resp) {
              console.log('resp',resp)
              frm.refresh_field('items')
              frm.refresh_field('tariff_number_summary')
              if (resp){
                frm.trigger("reference_document")
                frm.dirty()
                // frm.save()
                // frappe.msgprint(__('Document updated successfully'));
              }
            },
          });
        });
        }
    
        console.log(frm.doc.company);
        frm.set_query("reference_doctype", () => {
          return {
            filters: [["name", "in", ["Purchase Invoice", "Purchase Receipt"]]],
          };
        });
        if (frm.doc.company && frm.doc.reference_doctype == "Purchase Invoice") {
          frm.set_query("reference_document", () => {
            return {
              filters: [
                ["company", "=", frm.doc.company],
                ["docstatus", "=", 1],
                ["update_stock", "=", 1],
              ],
            };
          });
        } else {
          frm.set_query("reference_document", () => {
            return {
              filters: [
                ["company", "=", frm.doc.company],
                ["docstatus", "=", 1],
              ],
              fields: ["reference_document", "creation"],
              order_by: "creation desc",
            };
          });
          console.log("ppppppppppppppppp");
        }
        frm.fields_dict["additional_charges"].grid.get_field(
          "expense_account"
        ).get_query = function (doc, cdt, cdn) {
          var child = locals[cdt][cdn];
          // console.log(child);
          return {
            filters: [
              [
                "account_type",
                "in",
                [
                  "Chargeable",
                  "Expense Account",
                  "Expenses Included In Asset Valuation",
                  "Expenses Included In Valuation",
                  "Income Account",
                  "Tax",
                ],
              ],
              ["company", "=", frm.doc.company],
            ],
          };
        };
      },
    
      item_details_tab: function (frm) {
        frm.refresh_field("items");
        frm.refresh_field("tariff_number_summary");
        frm.refresh_field("grand_total");
        frm.refresh_field("total_item_qty");
        frm.refresh_field("item_count");
      },
    });
    
    frappe.ui.form.on("Landed Cost Taxes and Charges", {
      expense_account: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        var comp = frm.doc.company;
        var currency = child.account_currency;
    
        frappe.db.get_doc("Company", comp).then(({ default_currency }) => {
          //console.log(default_currency)
          frappe.call({
            method: "erpnext.setup.utils.get_exchange_rate",
            args: {
              from_currency: currency,
              to_currency: default_currency,
            },
            callback: function (r) {
              if (r.message) {
                frappe.model.set_value(cdt, cdn, "exchange_rate", r.message);
                console.log(r.message);
              }
            },
          });
        });
      },
    });
    
    frappe.ui.form.on("Landed Cost Taxes and Charges", {
      amount: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        frappe.call({
          method: "get_exchange",
          doc: frm.doc,
          args: {
            exca: child.expense_account,
            amt: child.amount,
          },
          callback: function (resp) {
            console.log("resp************************", resp);
            // frappe.model.set_value(cdt,cdn,'account_currency',resp.message[0])
            // freight values to be based on usd from supplier
            // frappe.model.set_value(cdt,cdn,'exchange_rate',resp.message[1])
            frappe.model.set_value(cdt, cdn, "base_amount", resp.message[2]);
            // frappe.model.set_value(cdt,cdn,'account_currency',resp.message[3])
            frm.refresh_field("additional_charges");
          },
        });
      },
      expense_account: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        frappe.call({
          method: "get_exchange",
          doc: frm.doc,
          args: {
            exca: child.expense_account,
            amt: child.amount,
          },
          callback: function (resp) {
            console.log("---------------------", resp);
            // frappe.model.set_value(cdt,cdn,'account_currency',resp.message[0])
            frappe.model.set_value(cdt, cdn, "account_currency", resp.message[0]);
            frm.refresh_field("additional_charges");
          },
        });
      },
    });
    
    frappe.ui.form.on("Invoice Verification Item", {
      customs_tariff_number:function(frm){
        console.log("customs_tariff_number",frm.doc.reference_document)
        // if (frm.doc.reference_document) {
        //   frappe.call({
        //     method: "get_items_by_purchase_invoice",
        //     doc: frm.doc,
        //     callback: function (resp) {
        //       frm.refresh_field("items");
        //       frm.refresh_field("tariff_number_summary");
        //       frm.refresh_field("grand_total");
        //       frm.refresh_field("total_item_qty");
        //       frm.refresh_field("item_count");
        //       frm.refresh_field("currency");
        //       console.log(resp);
        //     },
        //   });
        // }
      }
    });  
