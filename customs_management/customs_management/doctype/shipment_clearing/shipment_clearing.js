// Copyright (c) 2023, Sudeep Kulkarni and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shipment Clearing', {
	onload_post_render: function(frm) {
		if(frm.doc.__islocal) {
			frappe.call({
				method: 'get_default_additional_charges',
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field('additional_charges');
				}
			});
		}
    },

	before_save: function(frm) {
		if(frm.doc.__islocal) {
			frappe.call({
				method: 'initialize_additional_charges',
				doc: frm.doc,
				callback:function(r) {
					frm.refresh_field('additional_charges');
				}
			});
		}
	},

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
    
	refresh: function(frm) {
        // Hides check boxes on child tables
        $('.row-check').hide();

        // TODO: 
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Go to Split up'), function () {
			  console.log('go to summary');
			  frappe.set_route(`app/print/Shipment Clearing/${frm.doc.name}`);
			});
		}

		frm.set_query('customs_entry', () => {
			return {
				filters: [
					['docstatus', '=', 1],
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
	},

    customs_entry: async function(frm) {
        await frappe.call({
            method: 'get_markup_summary',
            doc: frm.doc,
            callback: function(r) {
                frm.refresh_field('markup_summary');
            }
        });
        await frappe.call({
			method: 'update_default_additional_charges',
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field('additional_charges');
			}
		});
    },

	sales_pricelist: function(frm) {
        frappe.call({
            method: 'get_markup_summary',
            doc: frm.doc,
            callback: function(r) {
                frm.refresh_field('markup_summary');
            }
        });
	},

	bank_percentage: function(frm) {
        frappe.call({
            method: 'update_bank_and_handler_charges',
            doc: frm.doc,
            freeze: true,
			freeze_message: "Loading Bank Percentage Value...",
            callback: function(r) {
                frm.refresh_field('bank_percentage_value');
                frm.refresh_field('total_charges_amount');
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
				frm.refresh_field('handler_percentage_value');
				frm.refresh_field('total_charges_amount');
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

frappe.ui.form.on('Markup Summary', {
	markup_per: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		frappe.call({
            method: 'get_markup_summary',
			doc: frm.doc,
			args: {
                'item_tariff_number': child.tariff_number,
				'custom_markup_percentage': child.markup_per
			},
			callback: function(r) {
                frm.refresh_field('markup_summary');
            }
		});
	}
});

// TODO: 
frappe.ui.form.on('Price Revision', {
    approved: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
		console.log('hello')
		frappe.db.get_doc('Customs Management Settings').then(t => {
			var threshold = t.threshold; 
			console.log('if condition')
			frappe.model.set_value(cdt, cdn, 'price_approved',1);
			console.log('true')
			})
    },
    
	uom: function(frm){
		console.log('uom')
		frappe.call({
			method:'customs_management.api.conversion_uom_pricerevision',
			args:{
				row: frm.selected_doc
			},
			freeze:true,
			freeze_message:'Updating Values...',
			async:false,
			callback:function(res){
				console.log('res',res)
				if (res.message){
					console.log('inside if  for uom')
					let [qty,cp,up] = res.message
					frm.selected_doc.qty=qty
					frm.selected_doc.calculated_price=cp
					frm.selected_doc.updated_price=up
					frm.refresh_field('price_revision_items')
				}
			}

		})
	}
});