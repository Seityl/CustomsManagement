// Copyright (c) 2025, Jollys Pharmacy Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Costing", {
    onload: function(frm) {
        // Hides Add Row button from child tables
        frm.get_field('additional_charges').grid.cannot_add_rows = true;
        frm.get_field('markup_summary').grid.cannot_add_rows = true;
        frm.get_field('price_revision_items').grid.cannot_add_rows = true;
        // Hides Delete button from child tables
        frm.set_df_property('additional_charges', 'cannot_delete_rows', 1);
        frm.set_df_property('markup_summary', 'cannot_delete_rows', 1);
        frm.set_df_property('price_revision_items', 'cannot_delete_rows', 1);
    },
    
	refresh: async function(frm) {
        // Add a custom button to download the Price Revision table as PDF
        frm.add_custom_button(__('Download Price Revision PDF'), function() {
            downloadPriceRevisionPDF(frm);
        });
        
        if (frm.doc.__islocal) {
			frappe.call({
				method: 'get_default_additional_charges',
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field('additional_charges');
				}
			});
            
            if (frm.doc.customs_entry) {
                if (!frm.doc.bank_percentage) {
                    try {
                        let response = await frappe.call({
                            method: "frappe.client.get_value",
                            args: {
                                doctype: "Customs Management Settings",
                                fieldname: "default_bank_per"
                            }
                        });
                        if (response && response.message) {
                            frm.set_value("bank_percentage", parseInt(response.message.default_bank_per));
                        }
                    } catch (error) {
                        console.error("Error fetching default bank percentage:", error);
                        frappe.msgprint(__("Error fetching default bank percentage: {0}", [error]), "Error", "red");
                    }
                }
                if (!frm.doc.handler_percentage) {
                    try {
                        let response = await frappe.call({
                            method: "frappe.client.get_value",
                            args: {
                                doctype: "Customs Management Settings",
                                fieldname: "default_handler_per"
                            }
                        });
                        if (response && response.message) {
                            frm.set_value("handler_percentage", parseInt(response.message.default_handler_per));
                        }
                    } catch (error) {
                        console.error("Error fetching default handler percentage:", error);
                        frappe.msgprint(__("Error fetching default handler percentage: {0}", [error]), "Error", "red");
                    }
                }
            }
		}

        // Hides check boxes on child tables
        $('.row-check').hide();

        // TODO: 
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Go to Split up'), function () {
			  console.log('go to summary');
			  frappe.set_route(`app/print/Costing/${frm.doc.name}`);
			});
		}

		frm.set_query('customs_entry', () => {
			return {
				filters: [
					['docstatus', '=', 1],
					['costed', '=', 0]
			    ]
			};
		});

		frm.set_query('sales_pricelist', () => {
			return {
				filters: [
					['buying', '=', 0],
		    	]
			};
		});

		if(frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Generate Price Revision'), function() {
				frappe.call({
					method: 'generate_price_revision',
					doc: frm.doc,
					freeze: true,
					freeze_message: 'Loading Price Revision...',
					callback: function(r) {
						frm.save('Update');
						frm.refresh_field('price_revision_items');
					}
				});
			});
		}
        
        // Custom HTML Item Details Table
        frm.fields_dict.items.grid.update_footer = function() {
            let table_rows = '';
            let row_count = frm.doc.items.length;
            let processed_rows = 0;

            // Function to render the table with subtle theme-aware styling
            let renderTable = (table_rows) => {
                // Hide the original grid wrapper and remove previous custom wrappers
                $(frm.fields_dict.items.grid.wrapper).hide();
                let parent = $(frm.fields_dict.items.grid.wrapper).parent();
                parent.find('.custom-items-display-wrapper').remove();

                parent.append(`
                    <div class="custom-items-display-wrapper" style="overflow-x: auto; width: 100%; margin-top: 15px; background-color: var(--card-bg, #fff);">
                        <h4 style="font-weight: bold; margin-bottom: 10px; color: var(--text-color, #333);">Item Details</h4>
                        <table class="table table-bordered custom-items-display" 
                            style="border-radius: 10px; border: 3px solid var(--border-color, #dee2e6); width: 100%; background-color: var(--card-bg, #fff); color: var(--text-color, #333);">
                            <thead style="background-color: var(--header-bg, #f8f9fa); color: var(--header-text, #333);">
                                <tr style="font-weight: bold; border-bottom: 3px solid var(--border-color, #dee2e6);">
                                    <th>Reference Doctype</th>
                                    <th>Reference Document</th>
                                    <th>Item</th>
                                    <th>Item ID</th>
                                    <th>Description</th>
                                    <th>Tariff Number</th>
                                    <th>Duty Exempt</th>
                                    <th>Factor</th>
                                    <th>Rate</th>
                                    <th>Base Rate (XCD)</th>
                                    <th>Amount</th>
                                    <th>Base Amount (XCD)</th>
                                    <th>Invoice Currency</th>
                                    <th>Invoice Conversion Rate</th>
                                    <th>Invoice Number</th>
                                    <th>Cost Center</th>
                                    <th>UOM</th>
                                    <th>Qty</th>
                                    <th>Stock Qty</th>
                                    <th>Additional Charges</th>
                                    <th>Base Additional Charges (XCD)</th>
                                    <th>Miscellaneous</th>
                                    <th>Taxable Amount</th>
                                    <th>Base Taxable Amount (XCD)</th>
                                    <th>Duty %</th>
                                    <th>Duty Amount</th>
                                    <th>Base Duty Amount (XCD)</th>
                                    <th>VAT %</th>
                                    <th>VAT Amount</th>
                                    <th>Base VAT Amount (XCD)</th>
                                    <th>Service %</th>
                                    <th>Service Amount</th>
                                    <th>Base Service Amount (XCD)</th>
                                    <th>Surcharge %</th>
                                    <th>Surcharge Amount</th>
                                    <th>Base Surcharge Amount (XCD)</th>
                                    <th>Excise %</th>
                                    <th>Excise Amount</th>
                                    <th>Base Excise Amount (XCD)</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${table_rows}
                            </tbody>
                        </table>
                    </div>
                `);
            };

            // Function to process each row
            let processRow = (row) => {
                table_rows += `
                    <tr>
                        <td>${row.reference_doctype || ''}</td>
                        <td>${row.reference_document || ''}</td>
                        <td>${row.item || ''}</td>
                        <td>${row.item_id || ''}</td>
                        <td>${row.description || ''}</td>
                        <td>${row.customs_tariff_number || ''}</td>
                        <td>${row.duty_exempt ? 'Yes' : 'No'}</td>
                        <td>${row.item_weight || '0.00'}</td>
                        <td>${row.rate || '0.00'}</td>
                        <td>${row.base_rate || '0.00'}</td>
                        <td>${row.amount || '0.00'}</td>
                        <td>${row.base_amount || '0.00'}</td>
                        <td>${row.ref_document_currency || ''}</td>
                        <td>${row.ref_document_conversion_rate || '0.00'}</td>
                        <td>${row.supplier_invoice_no || ''}</td>
                        <td>${row.cost_center || ''}</td>
                        <td>${row.uom || ''}</td>
                        <td>${row.qty || '0'}</td>
                        <td>${row.stock_qty || '0'}</td>
                        <td>${row.additional_charges || '0.00'}</td>
                        <td>${row.base_additional_charges || '0.00'}</td>
                        <td>${row.miscellaneous || '0.00'}</td>
                        <td>${row.taxable_amount || '0.00'}</td>
                        <td>${row.base_taxable_amount || '0.00'}</td>
                        <td>${row.duty_percent || '0'}</td>
                        <td>${row.duty_amount || '0.00'}</td>
                        <td>${row.base_duty_amount || '0.00'}</td>
                        <td>${row.vat_percent || '0'}</td>
                        <td>${row.vat_amount || '0.00'}</td>
                        <td>${row.base_vat_amount || '0.00'}</td>
                        <td>${row.service_charge_percent || '0'}</td>
                        <td>${row.service_charge_percentage || '0.00'}</td>
                        <td>${row.base_service_charge_percentage || '0.00'}</td>
                        <td>${row.surcharge_percent || '0'}</td>
                        <td>${row.surcharge_percentage || '0.00'}</td>
                        <td>${row.base_surcharge_percentage || '0.00'}</td>
                        <td>${row.excise_percent || '0'}</td>
                        <td>${row.excise_percentage || '0.00'}</td>
                        <td>${row.base_excise_percentage || '0.00'}</td>
                    </tr>
                `;

                processed_rows++;

                // Once all rows are processed, render the table
                if (processed_rows === row_count) {
                    renderTable(table_rows);
                }
            };

            // Process each row
            frm.doc.items.forEach(row => {
                processRow(row);
            });
        };

        frm.fields_dict.items.grid.update_footer();

        // Custom HTML Price Revision Table
        frm.fields_dict.price_revision_items.grid.update_footer = function() {
            let table_rows = '';
            let row_count = frm.doc.price_revision_items.length;
            let processed_rows = 0;

            if (!row_count) {
                console.warn("No data in price_revision_items, skipping table render.");
                return;
            }

            let renderTable = (table_rows) => {
                $(frm.fields_dict.price_revision_items.grid.wrapper).hide();
                let parent = $(frm.fields_dict.price_revision_items.grid.wrapper).parent();
                parent.find('.custom-price-revision-items-wrapper').remove();
                parent.append(`
                    <div class="custom-price-revision-items-wrapper" style="overflow-x: auto; width: 100%; margin-top: 15px; background-color: var(--card-bg, #fff);">
                        <h4 style="font-weight: bold; margin-bottom: 10px; color: var(--text-color, #333);">Price Revision</h4>
                        <table class="table table-bordered custom-price-revision-items" 
                            style="border-radius: 10px; border: 3px solid var(--border-color, #dee2e6); width: 100%; background-color: var(--card-bg, #fff); color: var(--text-color, #333);">
                            <thead style="background-color: var(--header-bg, #f8f9fa); color: var(--header-text, #333);">
                                <tr>
                                    <th>Item</th>
                                    <th>Description</th>
                                    <th>Qty</th>
                                    <th>UOM</th>
                                    <th>Price</th>
                                    <th>Last Cost</th>
                                    <th>Calculated Price</th>
                                    <th colspan="2" style="text-align: left;">New Price</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${table_rows}
                            </tbody>
                        </table>
                    </div>
                `);
            };

            let processRow = (row) => {
                let input_id = `updated-price-${row.name}`;
                let button_id = `approve-btn-${row.name}`;
                let isApproved = row.price_approved;

                table_rows += `
                    <tr>
                        <td>${row.item || ''}</td>
                        <td>${row.description || ''}</td>
                        <td>${row.qty || ''}</td>
                        <td>${row.uom || ''}</td>
                        <td>${row.price ? row.price.toFixed(2) : '0.00'}</td>
                        <td>${row.current_price ? row.current_price.toFixed(2) : '0.00'}</td>
                        <td>${row.each_price ? row.each_price.toFixed(2) : ''}</td>
                        <td>
                            <input type="text" id="${input_id}" 
                                value="${row.updated_each_price ? row.updated_each_price.toFixed(2) : ''}" 
                                style="width: 80px;" ${isApproved ? "disabled" : ""} />
                        </td>
                        <td>
                            <button id="${button_id}" 
                                class="btn btn-xs ${isApproved ? 'btn-success' : 'btn-danger'}" 
                                onclick="approve_price_revision('${row.name}', '${input_id}', '${button_id}')">
                                ${isApproved ? "Unapprove" : "Approve"}
                            </button>
                        </td>
                    </tr>
                `;

                processed_rows++;

                if (processed_rows === row_count) {
                    renderTable(table_rows);
                }
            };

            frm.doc.price_revision_items.forEach(processRow);
        };

        frm.fields_dict.price_revision_items.grid.update_footer();
    },

    customs_entry:  function(frm) {
        frappe.call({
            method: 'get_markup_summary',
            doc: frm.doc,
            callback: function(r) {
                frm.refresh();
            }
        });
    },

    sales_pricelist: function(frm) {
        if (frm.doc.customs_entry) {
            frappe.call({
                method: "get_markup_summary",
                doc: frm.doc,
                callback: function (r) {
                    frm.refresh();
                }
            });
        } else {
            frappe.show_alert({
                message: __("Please attach a Customs Entry before proceeding."),
                indicator: "orange"
            });
        }
    },

	bank_percentage: function(frm) {
        frappe.call({
            method: 'update_bank_and_handler_charges',
            doc: frm.doc,
            freeze: true,
			freeze_message: "Loading Bank Percentage Value...",
            callback: function(r) {
                frm.refresh();
            }
        });
	},
	
	handler_percentage: function(frm) {
        frappe.call({
            method: 'update_bank_and_handler_charges',
			doc: frm.doc,
            freeze: true,
			freeze_message: "Loading Handler Percentage Value...",
			callback: function(r) {
                frm.refresh();
			}
		});
	}
});

frappe.ui.form.on('Landed Cost Taxes and Charges', {
	amount: function(frm, cdt, cdn) {
		frappe.call({
			method: 'update_default_additional_charges',
            freeze: true,
			freeze_message: "Loading Additional Charges...",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field('additional_charges');
			}
		});
	}
});

// frappe.ui.form.on('Markup Summary', {
// 	markup_per: function(frm, cdt, cdn) {
// 		var child = locals[cdt][cdn]
// 		frappe.call({
//             method: 'get_markup_summary',
// 			doc: frm.doc,
// 			args: {
//                 'item_tariff_number': child.tariff_number,
// 				'custom_markup_percentage': child.markup_per
// 			},
// 			callback: function(r) {
//                 frm.refresh_field('markup_summary');
//             }
// 		});
// 	}
// });

// Function to approve or unapprove price revision
window.approve_price_revision = function(row_id, input_id, button_id) {
    let new_price_input = $("#" + input_id).val();
    let new_price = parseFloat(new_price_input);
    let button = $("#" + button_id);

    frappe.model.with_doc("Costing", cur_frm.doc.name, function() {
        let price_revision_items = cur_frm.doc.price_revision_items;
        let row = price_revision_items.find(item => item.name === row_id);
        
        if (!row) {
            console.error("Row not found for row_id:", row_id);
            frappe.msgprint(`Row not found for ID: ${row_id}`);
            return;
        }

        // Validate new price before updating the document
        if (isNaN(new_price)) {
            console.error("Invalid new price:", new_price);
            frappe.msgprint("Please enter a valid number for the New Price.");
            return;
        }
        
        if (new_price === 0) {
            console.error("Invalid new price:", new_price);
            frappe.msgprint("Please enter a valid number for the New Price.");
            return;
        }

        let new_approval_status = !row.price_approved;
        
        if (new_approval_status) {
            $("#" + input_id).prop("disabled", true);
            button.removeClass("btn-danger").addClass("btn-success").text("Unapprove");
        } else {
            $("#" + input_id).prop("disabled", false);
            button.removeClass("btn-success").addClass("btn-danger").text("Approve");
        }

        // Update the child row directly
        row.price_approved = new_approval_status;
        row.updated_each_price = new_price;
        cur_frm.refresh_field("price_revision_items");
        cur_frm.dirty();

        // Save the document immediately after the update
        cur_frm.save('Update').then(() => {
            console.log("Document saved successfully after setting updated_each_price.");
        }).catch(err => {
            console.error("Error saving document after updating price:", err);
            frappe.msgprint("Error saving document: " + err.message);
        });

        cur_frm.refresh_field("price_revision_items");
    });
};

// Function to generate and download the PDF
function downloadPriceRevisionPDF(frm) {
    // The wrapper class for the custom HTML table; adjust if needed.
    let $tableWrapper = $(frm.fields_dict.price_revision_items.grid.wrapper).parent().find('.custom-price-revision-items-wrapper');
    
    if(!$tableWrapper.length) {
        frappe.msgprint("Price Revision table not found!");
        return;
    }
    
    // Use html2canvas to render the table into a canvas
    html2canvas($tableWrapper[0]).then(function(canvas) {
        // Convert the canvas to an image
        let imgData = canvas.toDataURL('image/png');
        // Create jsPDF instance (landscape orientation, A4 paper size)
        let pdf = new jsPDF('l', 'pt', 'a4');

        // Calculate width and height to fit A4
        let pageWidth = pdf.internal.pageSize.getWidth();
        let pageHeight = pdf.internal.pageSize.getHeight();
        // Optional: Scale image if necessary
        let imgWidth = pageWidth;
        let imgHeight = canvas.height * imgWidth / canvas.width;
        
        // Add image to PDF
        pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
        
        // Download the PDF
        pdf.save('Price_Revision.pdf');
    }).catch(function(err) {
        console.error("Error generating PDF: ", err);
        frappe.msgprint("Error generating PDF. Please check the browser console for details.");
    });
}