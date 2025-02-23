import frappe
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

@frappe.whitelist()
def sales_xml(name):
    print("name",name)
    sales=frappe.get_doc("Sales Invoice",name)
    # print("sales Contact",sales.contact_display,sales.address_display.replace("<br>"," "))
    asycuda = ET.Element("ASYCUDA")
    #######################Export release######################## 
    s_elem002 = ET.SubElement(asycuda, 'Export_release')
    s_elem0 = ET.SubElement(s_elem002, 'Date_of_exit')
    s_elem1 = ET.SubElement(s_elem002, 'Time_of_exit')
    s_elem2 = ET.SubElement(s_elem002, 'Actual_office_of_exit_code')
    s_elem3 = ET.SubElement(s_elem2, 'null')
    s_elem5 = ET.SubElement(s_elem002, 'Actual_office_of_exit_name')
    s_elem6 = ET.SubElement(s_elem5, 'null')
    s_elem8 = ET.SubElement(s_elem002, 'Exit_reference')
    ET.SubElement(s_elem8, 'null')
    s_elem11 = ET.SubElement(s_elem002, 'Comments')
    s_elem12 = ET.SubElement(s_elem11, 'null')
    #######################Assessment notice######################## 
    assessment_notice = ET.SubElement(asycuda, 'Assessment_notice')
    # Create the Registration_year sub-element
    registration_year = ET.SubElement(assessment_notice, 'Registration_year')
    registration_year.text = ''
    registration_year_null = ET.SubElement(registration_year, 'null')

    # Create the Assessment_year sub-element
    assessment_year = ET.SubElement(assessment_notice, 'Assessment_year')
    assessment_year.text = ''
    assessment_year_null = ET.SubElement(assessment_year, 'null')

    # Create the Total_item_taxes sub-element
    total_item_taxes = ET.SubElement(assessment_notice, 'Total_item_taxes')
    total_item_taxes.text = '1.5'

    # Create the Statement_number sub-element
    statement_number = ET.SubElement(assessment_notice, 'Statement_number')
    statement_number.text = ''
    statement_number_null = ET.SubElement(statement_number, 'null')

    # Create the Statement_date sub-element
    statement_date = ET.SubElement(assessment_notice, 'Statement_date')
    statement_date.text = ''

    # Create the Statement_serial sub-element
    statement_serial = ET.SubElement(assessment_notice, 'Statement_serial')
    statement_serial.text = ''
    statement_serial_null = ET.SubElement(statement_serial, 'null')

    #######################Assessment notice######################## 

    # Create the Items_taxes sub-element
    items_taxes = ET.SubElement(assessment_notice, 'Items_taxes')

    # Create the Item_tax sub-element
    item_tax = ET.SubElement(items_taxes, 'Item_tax')

    # Create the Tax_code sub-element
    tax_code = ET.SubElement(item_tax, 'Tax_code')
    tax_code.text = 'STD'

    # Create the Tax_description sub-element
    tax_description = ET.SubElement(item_tax, 'Tax_description')
    tax_description.text = 'STAMP DUTY'

    # Create the Tax_amount sub-element
    tax_amount = ET.SubElement(item_tax, 'Tax_amount')
    tax_amount.text = '1.5'

    # Create the Tax_mop sub-element
    tax_mop = ET.SubElement(item_tax, 'Tax_mop')
    tax_mop.text = '1'

    for i in range(13):
        # Create the Item_tax sub-element
        item_tax = ET.SubElement(items_taxes, 'Item_tax')

        # Create the Tax_code sub-element with null value
        tax_code = ET.SubElement(item_tax, 'Tax_code')
        tax_code_null = ET.SubElement(tax_code, 'null')

        # Create the Tax_description sub-element with null value
        tax_description = ET.SubElement(item_tax, 'Tax_description')
        tax_description_null = ET.SubElement(tax_description, 'null')

        # Create the Tax_amount sub-element
        tax_amount = ET.SubElement(item_tax, 'Tax_amount')
        tax_amount.text = ''

        # Create the Tax_mop sub-element with null value
        tax_mop = ET.SubElement(item_tax, 'Tax_mop')
        tax_mop_null = ET.SubElement(tax_mop, 'null')

    global_taxes = ET.SubElement(assessment_notice, 'Global_taxes')

    #######################Property########################

    # Create the Property sub-element under ASYCUDA
    property_element = ET.SubElement(asycuda, 'Property')

    # Create the Sad_flow sub-element
    sad_flow = ET.SubElement(property_element, 'Sad_flow')
    sad_flow.text = 'E'

    # Create the Forms sub-element
    forms = ET.SubElement(property_element, 'Forms')

    # Create the Number_of_the_form sub-element
    number_of_the_form = ET.SubElement(forms, 'Number_of_the_form')
    number_of_the_form.text = '1'

    # Create the Total_number_of_forms sub-element
    total_number_of_forms = ET.SubElement(forms, 'Total_number_of_forms')
    total_number_of_forms.text = '1'

    # Create the Nbers sub-element
    nbers = ET.SubElement(property_element, 'Nbers')

    # Create the Number_of_loading_lists sub-element
    number_of_loading_lists = ET.SubElement(nbers, 'Number_of_loading_lists')
    number_of_loading_lists.text = '0'

    # Create the Total_number_of_items sub-element
    total_number_of_items = ET.SubElement(nbers, 'Total_number_of_items')
    total_number_of_items.text = '1'

    # Create the Total_number_of_packages sub-element
    total_number_of_packages = ET.SubElement(nbers, 'Total_number_of_packages')
    total_number_of_packages.text = '1'

    # Create the Place_of_declaration sub-element
    place_of_declaration = ET.SubElement(property_element, 'Place_of_declaration')
    place_of_declaration_null = ET.SubElement(place_of_declaration, 'null')

    # Create the Date_of_declaration sub-element
    date_of_declaration = ET.SubElement(property_element, 'Date_of_declaration')

    # Create the Selected_page sub-element
    selected_page = ET.SubElement(property_element, 'Selected_page')
    selected_page.text = '1'
    #######################Identification########################
    # Create the Identification sub-element under ASYCUDA
    identification_element = ET.SubElement(asycuda, 'Identification')

    # Create the Office_segment sub-element
    office_segment = ET.SubElement(identification_element, 'Office_segment')

    # Create the Customs_clearance_office_code sub-element
    customs_clearance_office_code = ET.SubElement(office_segment, 'Customs_clearance_office_code')
    customs_clearance_office_code.text = sales.custom_customs_clearence_office


    # Create the Customs_Clearance_office_name sub-element
    customs_clearance_office_name = ET.SubElement(office_segment, 'Customs_Clearance_office_name')
    customs_clearance_office_name.text = frappe.db.get_value("Office Code",{"name":sales.custom_customs_clearence_office},['office_name'])

    # Create the Type sub-element
    type_element = ET.SubElement(identification_element, 'Type')

    # Create the Type_of_declaration sub-element
    type_of_declaration = ET.SubElement(type_element, 'Type_of_declaration')
    type_of_declaration.text = frappe.db.get_value("Declaration Gen Procedure",{"name":sales.custom_declaration_procedure},['name1'])

    # Create the Declaration_gen_procedure_code sub-element
    declaration_gen_procedure_code = ET.SubElement(type_element, 'Declaration_gen_procedure_code')
    declaration_gen_procedure_code.text = sales.custom_declaration_procedure

    # Create the Type_of_transit_document sub-element
    type_of_transit_document = ET.SubElement(type_element, 'Type_of_transit_document')
    type_of_transit_document_null = ET.SubElement(type_of_transit_document, 'null')

    # Create the Manifest_reference_number sub-element
    manifest_reference_number = ET.SubElement(identification_element, 'Manifest_reference_number')
    manifest_reference_number_null = ET.SubElement(manifest_reference_number, 'null')

    # Create the Registration sub-element
    registration = ET.SubElement(identification_element, 'Registration')

    # Create the Serial_number sub-element for Registration
    registration_serial_number = ET.SubElement(registration, 'Serial_number')
    registration_serial_number_null = ET.SubElement(registration_serial_number, 'null')

    # Create the Number sub-element for Registration
    registration_number = ET.SubElement(registration, 'Number')
    registration_number.text = ''

    # Create the Date sub-element for Registration
    registration_date = ET.SubElement(registration, 'Date')
    registration_date.text = ''

    # Create the Assessment sub-element
    assessment = ET.SubElement(identification_element, 'Assessment')

    # Create the Serial_number sub-element for Assessment
    assessment_serial_number = ET.SubElement(assessment, 'Serial_number')
    assessment_serial_number_null = ET.SubElement(assessment_serial_number, 'null')

    # Create the Number sub-element for Assessment
    assessment_number = ET.SubElement(assessment, 'Number')
    assessment_number.text = ''

    # Create the Date sub-element for Assessment
    assessment_date = ET.SubElement(assessment, 'Date')
    assessment_date.text = ''

    # Create the receipt sub-element
    receipt = ET.SubElement(identification_element, 'receipt')

    # Create the Serial_number sub-element for receipt
    receipt_serial_number = ET.SubElement(receipt, 'Serial_number')
    receipt_serial_number_null = ET.SubElement(receipt_serial_number, 'null')

    # Create the Number sub-element for receipt
    receipt_number = ET.SubElement(receipt, 'Number')
    receipt_number.text = ''

    # Create the Date sub-element for receipt
    receipt_date = ET.SubElement(receipt, 'Date')
    receipt_date.text = ''
    #######################Traders########################

    # Create the Traders sub-element under ASYCUDA
    traders_element = ET.SubElement(asycuda, 'Traders')

    # Create the Exporter sub-element
    exporter_element = ET.SubElement(traders_element, 'Exporter')

    # Create the Exporter_code sub-element
    exporter_code = ET.SubElement(exporter_element, 'Exporter_code')
    exporter_code.text = '0000036000003'

    # Create the Exporter_name sub-element
    exporter_name = ET.SubElement(exporter_element, 'Exporter_name')
    exporter_name.text = "JOLLY'S PHARMACY\n8 KING GEORGE V STREET\nROSEAU\n0000033"

    # Create the Consignee sub-element
    consignee_element = ET.SubElement(traders_element, 'Consignee')

    # Create the Consignee_code sub-element
    consignee_code = ET.SubElement(consignee_element, 'Consignee_code')
    consignee_code.text = ''



    # Create the Consignee_name sub-element
    consignee_name = ET.SubElement(consignee_element, 'Consignee_name')
    consignee_name.text = f"{(sales.address_display.replace('<br>',' ')).upper()} {(sales.contact_display).upper()}" if sales.address_display and sales.contact_display else ""

    # Create the Financial sub-element
    financial_element = ET.SubElement(traders_element, 'Financial')

    # Create the Financial_code sub-element
    financial_code = ET.SubElement(financial_element, 'Financial_code')
    financial_code_null = ET.SubElement(financial_code, 'null')

    # Create the Financial_name sub-element
    financial_name = ET.SubElement(financial_element, 'Financial_name')
    financial_name_null = ET.SubElement(financial_name, 'null')
    # #######################Traders########################
    # # Create the Traders sub-element under ASYCUDA
    # traders_element = ET.SubElement(asycuda, 'Traders')

    # # Create the Exporter sub-element
    # exporter_element = ET.SubElement(traders_element, 'Exporter')

    # # Create the Exporter_code sub-element
    # exporter_code = ET.SubElement(exporter_element, 'Exporter_code')
    # exporter_code.text = '0000036000003'

    # # Create the Exporter_name sub-element
    # exporter_name = ET.SubElement(exporter_element, 'Exporter_name')
    # exporter_name.text = "JOLLY'S PHARMACY\n8 KING GEORGE V STREET\nROSEAU\n0000033"

    # # Create the Consignee sub-element
    # consignee_element = ET.SubElement(traders_element, 'Consignee')

    # # Create the Consignee_code sub-element
    # consignee_code = ET.SubElement(consignee_element, 'Consignee_code')
    # consignee_code.text = ''

    # # Create the Consignee_name sub-element
    # consignee_name = ET.SubElement(consignee_element, 'Consignee_name')
    # consignee_name.text = "A JEAN VIDAL\n15769 EDGEWOOD DRIVE\nDUMFRIES, VA 22025\nUNITED STATES (US)"

    # # Create the Financial sub-element
    # financial_element = ET.SubElement(traders_element, 'Financial')

    # # Create the Financial_code sub-element
    # financial_code = ET.SubElement(financial_element, 'Financial_code')
    # financial_code_null = ET.SubElement(financial_code, 'null')

    # # Create the Financial_name sub-element
    # financial_name = ET.SubElement(financial_element, 'Financial_name')
    # financial_name_null = ET.SubElement(financial_name, 'null')
    #######################Declarant########################
    # Create the Declarant sub-element under ASYCUDA
    declarant_element = ET.SubElement(asycuda, 'Declarant')

    # Create the Declarant_code sub-element
    declarant_code = ET.SubElement(declarant_element, 'Declarant_code')
    declarant_code.text = '0000036000003'

    # Create the Declarant_name sub-element
    declarant_name = ET.SubElement(declarant_element, 'Declarant_name')
    declarant_name.text = "JOLLY'S PHARMACY\n8 KING GEORGE V STREET\nROSEAU"

    # Create the Declarant_representative sub-element
    declarant_representative = ET.SubElement(declarant_element, 'Declarant_representative')
    declarant_representative.text = 'Orrin Jolly'

    # Create the Reference sub-element
    reference_element = ET.SubElement(declarant_element, 'Reference')

    # Create the Year sub-element under Reference
    year = ET.SubElement(reference_element, 'Year')
    year.text = str(datetime.now().year)

    # Create the Number sub-element under Reference
    number = ET.SubElement(reference_element, 'Number')
    number.text = str(sales.custom_invoice_number)

    #######################General information######################## 
    # Create the General_information sub-element under ASYCUDA
    general_information_element = ET.SubElement(asycuda, 'General_information')

    # Create the Country sub-element
    country_element = ET.SubElement(general_information_element, 'Country')

    # Create the Country_first_destination sub-element
    country_first_destination = ET.SubElement(country_element, 'Country_first_destination')
    cfd_code = frappe.db.get_value("Country",{"name":sales.custom_country_first_destination},['code'])
    country_first_destination.text = cfd_code

    # Create the Trading_country sub-element
    trading_country = ET.SubElement(country_element, 'Trading_country')
    trading_country.text = ''

    # Create the Export sub-element
    export_element = ET.SubElement(country_element, 'Export')

    # Create the Export_country_code sub-element
    export_country_code = ET.SubElement(export_element, 'Export_country_code')
    export_country_code.text = 'DM'

    # Create the Export_country_name sub-element
    export_country_name = ET.SubElement(export_element, 'Export_country_name')
    export_country_name.text = 'Dominica'

    # Create the Export_country_region sub-element
    export_country_region = ET.SubElement(export_element, 'Export_country_region')
    export_country_region_null = ET.SubElement(export_country_region, 'null')

    # Create the Destination sub-element
    destination_element = ET.SubElement(country_element, 'Destination')

    # Create the Destination_country_code sub-element
    destination_country_code = ET.SubElement(destination_element, 'Destination_country_code')
    destination_country_code.text = cfd_code

    # Create the Destination_country_name sub-element
    destination_country_name = ET.SubElement(destination_element, 'Destination_country_name')
    destination_country_name.text = sales.custom_country_first_destination.upper()

    # Create the Destination_country_region sub-element
    destination_country_region = ET.SubElement(destination_element, 'Destination_country_region')
    destination_country_region.text = ''

    # Create the Country_of_origin_name sub-element
    country_of_origin_name = ET.SubElement(country_element, 'Country_of_origin_name')
    country_of_origin_name.text = sales.custom_country_of_origin

    # Create the Value_details sub-element
    value_details = ET.SubElement(general_information_element, 'Value_details')
    value_details.text = ''

    # Create the CAP sub-element
    cap = ET.SubElement(general_information_element, 'CAP')
    cap.text = ''

    # Create the Additional_information sub-element
    additional_information = ET.SubElement(general_information_element, 'Additional_information')
    additional_information_null = ET.SubElement(additional_information, 'null')

    # Create the Comments_free_text sub-element
    comments_free_text = ET.SubElement(general_information_element, 'Comments_free_text')
    comments_free_text_null = ET.SubElement(comments_free_text, 'null')
    #######################Transport######################## 
    # Create the Transport sub-element under ASYCUDA
    transport_element = ET.SubElement(asycuda, 'Transport')

    # Create the Means_of_transport sub-element
    means_of_transport = ET.SubElement(transport_element, 'Means_of_transport')

    # Create the Departure_arrival_information sub-element
    departure_arrival_information = ET.SubElement(means_of_transport, 'Departure_arrival_information')

    # Create the Identity sub-element under Departure_arrival_information
    identity = ET.SubElement(departure_arrival_information, 'Identity')
    identity.text = sales.custom_transport_service

    # Create the Nationality sub-element under Departure_arrival_information
    nationality = ET.SubElement(departure_arrival_information, 'Nationality')
    nationality_null = ET.SubElement(nationality, 'null')

    # Create the Border_information sub-element
    border_information = ET.SubElement(means_of_transport, 'Border_information')

    # Create the Identity sub-element under Border_information
    border_identity = ET.SubElement(border_information, 'Identity')
    border_identity.text = ''

    # Create the Nationality sub-element under Border_information
    border_nationality = ET.SubElement(border_information, 'Nationality')
    border_nationality.text = ''

    # Create the Mode sub-element under Border_information
    mode = ET.SubElement(border_information, 'Mode')
    mode.text = '4'

    # Create the Inland_mode_of_transport sub-element
    inland_mode_of_transport = ET.SubElement(means_of_transport, 'Inland_mode_of_transport')
    inland_mode_of_transport_null = ET.SubElement(inland_mode_of_transport, 'null')

    # Create the Container_flag sub-element
    container_flag = ET.SubElement(transport_element, 'Container_flag')
    container_flag.text = 'false'

    # Create the Delivery_terms sub-element
    delivery_terms = ET.SubElement(transport_element, 'Delivery_terms')

    # Create the Code sub-element under Delivery_terms
    delivery_terms_code = ET.SubElement(delivery_terms, 'Code')
    delivery_terms_code_null = ET.SubElement(delivery_terms_code, 'null')

    # Create the Place sub-element under Delivery_terms
    delivery_terms_place = ET.SubElement(delivery_terms, 'Place')
    delivery_terms_place_null = ET.SubElement(delivery_terms_place, 'null')

    # Create the Situation sub-element under Delivery_terms
    delivery_terms_situation = ET.SubElement(delivery_terms, 'Situation')
    delivery_terms_situation_null = ET.SubElement(delivery_terms_situation, 'null')

    # Create the Border_office sub-element
    border_office = ET.SubElement(transport_element, 'Border_office')

    # Create the Code sub-element under Border_office
    border_office_code = ET.SubElement(border_office, 'Code')
    border_office_code_null = ET.SubElement(border_office_code, 'null')

    # Create the Name sub-element under Border_office
    border_office_name = ET.SubElement(border_office, 'Name')
    border_office_name_null = ET.SubElement(border_office_name, 'null')

    # Create the Place_of_loading sub-element
    place_of_loading = ET.SubElement(transport_element, 'Place_of_loading')

    # Create the Code sub-element under Place_of_loading
    place_of_loading_code = ET.SubElement(place_of_loading, 'Code')
    place_of_loading_code_null = ET.SubElement(place_of_loading_code, 'null')

    # Create the Name sub-element under Place_of_loading
    place_of_loading_name = ET.SubElement(place_of_loading, 'Name')
    place_of_loading_name_null = ET.SubElement(place_of_loading_name, 'null')

    # Create the Country sub-element under Place_of_loading
    place_of_loading_country = ET.SubElement(place_of_loading, 'Country')
    place_of_loading_country.text = ''

    # Create the Location_of_goods sub-element
    location_of_goods = ET.SubElement(transport_element, 'Location_of_goods')
    location_of_goods_null = ET.SubElement(location_of_goods, 'null')
    #######################Financial######################## 
    # Create the Financial sub-element under ASYCUDA
    financial_element = ET.SubElement(asycuda, 'Financial')

    # Create the Financial_transaction sub-element
    financial_transaction = ET.SubElement(financial_element, 'Financial_transaction')

    # Create the code1 sub-element under Financial_transaction
    code1 = ET.SubElement(financial_transaction, 'code1')
    code1_null = ET.SubElement(code1, 'null')

    # Create the code2 sub-element under Financial_transaction
    code2 = ET.SubElement(financial_transaction, 'code2')
    code2_null = ET.SubElement(code2, 'null')

    # Create the Bank sub-element
    bank = ET.SubElement(financial_element, 'Bank')

    # Create the Code sub-element under Bank
    bank_code = ET.SubElement(bank, 'Code')
    bank_code_null = ET.SubElement(bank_code, 'null')

    # Create the Name sub-element under Bank
    bank_name = ET.SubElement(bank, 'Name')
    bank_name_null = ET.SubElement(bank_name, 'null')

    # Create the Branch sub-element under Bank
    bank_branch = ET.SubElement(bank, 'Branch')
    bank_branch.text = ''

    # Create the Reference sub-element under Bank
    bank_reference = ET.SubElement(bank, 'Reference')
    bank_reference.text = ''

    # Create the Terms sub-element
    terms = ET.SubElement(financial_element, 'Terms')

    # Create the Code sub-element under Terms
    terms_code = ET.SubElement(terms, 'Code')
    terms_code_null = ET.SubElement(terms_code, 'null')

    # Create the Description sub-element under Terms
    terms_description = ET.SubElement(terms, 'Description')
    terms_description_null = ET.SubElement(terms_description, 'null')

    # Create the Total_invoice sub-element
    total_invoice = ET.SubElement(financial_element, 'Total_invoice')
    total_invoice.text = ''

    # Create the Deffered_payment_reference sub-element
    deferred_payment_reference = ET.SubElement(financial_element, 'Deffered_payment_reference')
    deferred_payment_reference.text = '0000036000003'

    # Create the Mode_of_payment sub-element
    mode_of_payment = ET.SubElement(financial_element, 'Mode_of_payment')
    mode_of_payment.text = 'ACCOUNT PAYMENT'

    # Create the Amounts sub-element
    amounts = ET.SubElement(financial_element, 'Amounts')

    # Create the Total_manual_taxes sub-element under Amounts
    total_manual_taxes = ET.SubElement(amounts, 'Total_manual_taxes')
    total_manual_taxes.text = ''

    # Create the Global_taxes sub-element under Amounts
    global_taxes = ET.SubElement(amounts, 'Global_taxes')
    global_taxes.text = '0.0'

    # Create the Totals_taxes sub-element under Amounts
    totals_taxes = ET.SubElement(amounts, 'Totals_taxes')
    totals_taxes.text = '1.5'

    # Create the Guarantee sub-element
    guarantee = ET.SubElement(financial_element, 'Guarantee')

    # Create the Name sub-element under Guarantee
    guarantee_name = ET.SubElement(guarantee, 'Name')
    guarantee_name_null = ET.SubElement(guarantee_name, 'null')

    # Create the Amount sub-element under Guarantee
    guarantee_amount = ET.SubElement(guarantee, 'Amount')
    guarantee_amount.text = '0.0'

    # Create the Date sub-element under Guarantee
    guarantee_date = ET.SubElement(guarantee, 'Date')
    guarantee_date.text = ''

    # Create the Excluded_country sub-element under Guarantee
    excluded_country = ET.SubElement(guarantee, 'Excluded_country')

    # Create the Code sub-element under Excluded_country
    excluded_country_code = ET.SubElement(excluded_country, 'Code')
    excluded_country_code_null = ET.SubElement(excluded_country_code, 'null')

    # Create the Name sub-element under Excluded_country
    excluded_country_name = ET.SubElement(excluded_country, 'Name')
    excluded_country_name_null = ET.SubElement(excluded_country_name, 'null')
    #######################Warehouse######################## 
    # Create the Warehouse sub-element under ASYCUDA
    warehouse_element = ET.SubElement(asycuda, 'Warehouse')

    # Create the Identification sub-element under Warehouse
    identification_element = ET.SubElement(warehouse_element, 'Identification')

    # Create the null sub-element under Identification
    identification_null = ET.SubElement(identification_element, 'null')

    # Create the Delay sub-element under Warehouse
    delay_element = ET.SubElement(warehouse_element, 'Delay')
    delay_element.text = ''
    #######################Transit######################## 
    # Create the Transit sub-element under ASYCUDA
    transit_element = ET.SubElement(asycuda, 'Transit')

    # Create the Principal sub-element
    principal = ET.SubElement(transit_element, 'Principal')

    # Create the Code sub-element under Principal
    principal_code = ET.SubElement(principal, 'Code')
    principal_code_null = ET.SubElement(principal_code, 'null')

    # Create the Name sub-element under Principal
    principal_name = ET.SubElement(principal, 'Name')
    principal_name_null = ET.SubElement(principal_name, 'null')

    # Create the Representative sub-element under Principal
    representative = ET.SubElement(principal, 'Representative')
    representative_null = ET.SubElement(representative, 'null')

    # Create the Signature sub-element
    signature = ET.SubElement(transit_element, 'Signature')

    # Create the Place sub-element under Signature
    signature_place = ET.SubElement(signature, 'Place')
    signature_place_null = ET.SubElement(signature_place, 'null')

    # Create the Date sub-element under Signature
    signature_date = ET.SubElement(signature, 'Date')
    signature_date.text = ''

    # Create the Destination sub-element
    destination = ET.SubElement(transit_element, 'Destination')

    # Create the Office sub-element under Destination
    destination_office = ET.SubElement(destination, 'Office')
    destination_office_null = ET.SubElement(destination_office, 'null')

    # Create the Country sub-element under Destination
    destination_country = ET.SubElement(destination, 'Country')
    destination_country_null = ET.SubElement(destination_country, 'null')

    # Create the Seals sub-element
    seals = ET.SubElement(transit_element, 'Seals')

    # Create the Number sub-element under Seals
    seals_number = ET.SubElement(seals, 'Number')
    seals_number.text = ''

    # Create the Identity sub-element under Seals
    seals_identity = ET.SubElement(seals, 'Identity')
    seals_identity_null = ET.SubElement(seals_identity, 'null')

    # Create the Result_of_control sub-element
    result_of_control = ET.SubElement(transit_element, 'Result_of_control')
    result_of_control.text = ''

    # Create the Time_limit sub-element
    time_limit = ET.SubElement(transit_element, 'Time_limit')
    time_limit.text = ''

    # Create the Officer_name sub-element
    officer_name = ET.SubElement(transit_element, 'Officer_name')
    officer_name_null = ET.SubElement(officer_name, 'null')

    #######################Valuation######################## 
    # Create the Valuation sub-element under ASYCUDA
    valuation_element = ET.SubElement(asycuda, 'Valuation')

    # Create the Calculation_working_mode sub-element
    calculation_working_mode = ET.SubElement(valuation_element, 'Calculation_working_mode')
    calculation_working_mode.text = '0'

    # Create the Weight sub-element
    weight = ET.SubElement(valuation_element, 'Weight')

    # Create the Gross_weight sub-element under Weight
    gross_weight = ET.SubElement(weight, 'Gross_weight')
    gross_weight.text = ''

    # Create the Total_cost sub-element
    total_cost = ET.SubElement(valuation_element, 'Total_cost')
    total_cost.text = '101.07'

    # Create the Total_CIF sub-element
    total_cif = ET.SubElement(valuation_element, 'Total_CIF')
    total_cif.text = '133.08'

    # Create the Gs_Invoice sub-element
    gs_invoice = ET.SubElement(valuation_element, 'Gs_Invoice')

    # Create the Amount_national_currency sub-element under Gs_Invoice
    gs_invoice_amount_national_currency = ET.SubElement(gs_invoice, 'Amount_national_currency')
    gs_invoice_amount_national_currency.text = str(sales.base_grand_total)

    # Create the Amount_foreign_currency sub-element under Gs_Invoice
    gs_invoice_amount_foreign_currency = ET.SubElement(gs_invoice, 'Amount_foreign_currency')
    gs_invoice_amount_foreign_currency.text = str(sales.grand_total)

    # Create the Currency_code sub-element under Gs_Invoice
    gs_invoice_currency_code = ET.SubElement(gs_invoice, 'Currency_code')
    gs_invoice_currency_code.text = sales.currency

    # Create the Currency_name sub-element under Gs_Invoice
    gs_invoice_currency_name = ET.SubElement(gs_invoice, 'Currency_name')
    gs_invoice_currency_name.text = 'No foreign currency'

    # Create the Currency_rate sub-element under Gs_Invoice
    gs_invoice_currency_rate = ET.SubElement(gs_invoice, 'Currency_rate')
    gs_invoice_currency_rate.text = str(sales.conversion_rate)

    # Create and append Gs_external_freight element
    gs_external_freight = ET.SubElement(valuation_element, "Gs_external_freight")
    ET.SubElement(gs_external_freight, "Amount_national_currency").text = "0.0"
    ET.SubElement(gs_external_freight, "Amount_foreign_currency").text = "0"
    ET.SubElement(gs_external_freight, "Currency_code").text = ""
    ET.SubElement(gs_external_freight, "Currency_name").text = "No foreign currency"
    ET.SubElement(gs_external_freight, "Currency_rate").text = "0.0"

    # Create and append Gs_internal_freight element
    gs_internal_freight = ET.SubElement(valuation_element, "Gs_internal_freight")
    ET.SubElement(gs_internal_freight, "Amount_national_currency").text = "0.0"
    ET.SubElement(gs_internal_freight, "Amount_foreign_currency").text = "0.0"
    ET.SubElement(gs_internal_freight, "Currency_code").text = ""
    ET.SubElement(gs_internal_freight, "Currency_name").text = "No foreign currency"
    ET.SubElement(gs_internal_freight, "Currency_rate").text = "0.0"

    # Create and append Gs_insurance element
    gs_insurance = ET.SubElement(valuation_element, "Gs_insurance")
    ET.SubElement(gs_insurance, "Amount_national_currency").text = "0.0"
    ET.SubElement(gs_insurance, "Amount_foreign_currency").text = "0"
    ET.SubElement(gs_insurance, "Currency_code").text = ""
    ET.SubElement(gs_insurance, "Currency_name").text = "No foreign currency"
    ET.SubElement(gs_insurance, "Currency_rate").text = "0.0"

    # Create and append Gs_other_cost element
    gs_other_cost = ET.SubElement(valuation_element, "Gs_other_cost")
    ET.SubElement(gs_other_cost, "Amount_national_currency").text = "0.0"
    ET.SubElement(gs_other_cost, "Amount_foreign_currency").text = "0"
    ET.SubElement(gs_other_cost, "Currency_code").text = ""
    ET.SubElement(gs_other_cost, "Currency_name").text = "No foreign currency"
    ET.SubElement(gs_other_cost, "Currency_rate").text = "0.0"

    # Create and append Gs_deduction element
    gs_deduction = ET.SubElement(valuation_element, "Gs_deduction")
    ET.SubElement(gs_deduction, "Amount_national_currency").text = "0.0"
    ET.SubElement(gs_deduction, "Amount_foreign_currency").text = "0"
    ET.SubElement(gs_deduction, "Currency_code").text = ""
    ET.SubElement(gs_deduction, "Currency_name").text = "No foreign currency"
    ET.SubElement(gs_deduction, "Currency_rate").text = "0.0"

    # Create the Total sub-element
    total = ET.SubElement(valuation_element, 'Total')

    # Create the Total_invoice sub-element under Total
    total_invoice = ET.SubElement(total, 'Total_invoice')
    total_invoice.text = '11.78'

    # Create the Total_weight sub-element under Total
    total_weight = ET.SubElement(total, 'Total_weight')
    total_weight.text = '1.0'

    #######################Item######################## 
    def tariff_data():
        items=[]
        for i in sales.items:
            print(i.item_code)
            print(i.__dict__)
            tn=frappe.db.get_value('Item',{"name":i.get('item_code')},['customs_tariff_number'])
            i.__dict__['tariff_number']=tn if tn else None
            items.append(i.__dict__)
        print("items of tariff",items)
        dic={}
        for i in items:
            if i.get('tariff_number'):
                if i.get(i.get('tariff_number')) in dic:
                    dic[i.get('tariff_number')]['qty']+=i.get('qty')
                    dic[i.get('tariff_number')]['amount']+=i.get('amount')
                    dic[i.get('tariff_number')]['base_amount']+=i.get('base_amount')
                else:
                    tariff_desc,tariff_prec=frappe.db.get_value("Customs Tariff Number",{"name":i.get('tariff_number')},['description','custom_precision'])
                    dic[i.get('tariff_number')]=i
                    dic[i.get('tariff_number')]['tariff_description']= tariff_desc
                    dic[i.get('tariff_number')]['tariff_precision']= tariff_prec if tariff_prec else '00'
        print("dic",dic)
        return dic
    unit_weight=sales.custom_gross_weight/sales.total_qty
    tariff_dic=tariff_data()
    tariff_no_list=list(tariff_dic.keys())
    tariff_no_list.sort()
    print('tariff no list',tariff_no_list)
    # frappe.throw("manual error")
    for data in tariff_no_list:
        tariff_data=tariff_dic.get(data)
        if not tariff_data:
            continue
        # Create the Item sub-element under ASYCUDA
        item_element = ET.SubElement(asycuda, 'Item')

        # Create the Packages sub-element
        packages = ET.SubElement(item_element, 'Packages')

        # Create the Number_of_packages sub-element under Packages
        number_of_packages = ET.SubElement(packages, 'Number_of_packages')
        number_of_packages.text = str(sales.custom_number_of_packages)

        # Create the Marks1_of_packages sub-element under Packages
        marks1_of_packages = ET.SubElement(packages, 'Marks1_of_packages')
        marks1_of_packages.text = sales.contact_display.upper() if sales.contact_display else ""

        # Create the Marks2_of_packages sub-element under Packages
        marks2_of_packages = ET.SubElement(packages, 'Marks2_of_packages')
        marks2_of_packages_null = ET.SubElement(marks2_of_packages, 'null')

        # Create the Kind_of_packages_code sub-element under Packages
        kind_of_packages_code = ET.SubElement(packages, 'Kind_of_packages_code')
        kind_of_packages_code.text = sales.custom_package_type

        # Create the Kind_of_packages_name sub-element under Packages
        kind_of_packages_name = ET.SubElement(packages, 'Kind_of_packages_name')
        kind_of_packages_name.text = frappe.db.get_value("Package Type",{"name":sales.custom_package_type},['package_type'])


        # Create the IncoTerms sub-element
        inco_terms = ET.SubElement(item_element, 'IncoTerms')

        # Create the Code sub-element under IncoTerms
        inco_terms_code = ET.SubElement(inco_terms, 'Code')
        inco_terms_code_null = ET.SubElement(inco_terms_code, 'null')

        # Create the Place sub-element under IncoTerms
        inco_terms_place = ET.SubElement(inco_terms, 'Place')
        inco_terms_place_null = ET.SubElement(inco_terms_place, 'null')

        # Create the Tarification sub-element
        tarification = ET.SubElement(item_element, 'Tarification')

        # Create the Tarification_data sub-element under Tarification
        tarification_data = ET.SubElement(tarification, 'Tarification_data')
        tarification_data_null = ET.SubElement(tarification_data, 'null')

        # Create the HScode sub-element under Tarification
        hscode = ET.SubElement(tarification, 'HScode')

        # Create the Commodity_code sub-element under HScode
        commodity_code = ET.SubElement(hscode, 'Commodity_code')
        commodity_code.text = data.replace('.','')[0:-1]

        # Create sub-elements Precision_1, Precision_2, Precision_3, and Precision_4 under HScode
        precision_1 = ET.SubElement(hscode, 'Precision_1')
        precision_1.text = '00'

        precision_2 = ET.SubElement(hscode, 'Precision_2')
        precision_2_null = ET.SubElement(precision_2, 'null')

        precision_3 = ET.SubElement(hscode, 'Precision_3')
        precision_3_null = ET.SubElement(precision_3, 'null')

        precision_4 = ET.SubElement(hscode, 'Precision_4')
        precision_4_null = ET.SubElement(precision_4, 'null')

        # Add the Preference_code sub-element under Tarification
        preference_code = ET.SubElement(tarification, 'Preference_code')
        preference_code_null = ET.SubElement(preference_code, 'null')

        # Add the Extended_customs_procedure sub-element under Tarification
        extended_customs_procedure = ET.SubElement(tarification, 'Extended_customs_procedure')
        extended_customs_procedure.text = sales.custom_extended_customs

        # Add the National_customs_procedure sub-element under Tarification
        national_customs_procedure = ET.SubElement(tarification, 'National_customs_procedure')
        national_customs_procedure.text = sales.custom_national_customs_procedure

        # Add the Quota sub-element under Tarification
        quota = ET.SubElement(tarification, 'Quota')
        quota_code = ET.SubElement(quota, 'QuotaCode')
        quota_code_null = ET.SubElement(quota_code, 'null')

        # Add the Supplementary_unit elements under Tarification
        for i in range(1, 4):
            supplementary_unit = ET.SubElement(tarification, 'Supplementary_unit')
            supplementary_unit_rank = ET.SubElement(supplementary_unit, 'Supplementary_unit_rank')
            supplementary_unit_rank.text = str(i)
            supplementary_unit_code = ET.SubElement(supplementary_unit, 'Suppplementary_unit_code')
            if i == 1:
                supplementary_unit_code.text = tariff_data.get('uom')
            else:
                supplementary_unit_code_null = ET.SubElement(supplementary_unit_code, 'null')
            supplementary_unit_name = ET.SubElement(supplementary_unit, 'Suppplementary_unit_name')
            if i == 1:
                supplementary_unit_name.text = tariff_data.get('uom')
            supplementary_unit_quantity = ET.SubElement(supplementary_unit, 'Suppplementary_unit_quantity')
            if i == 1:
                supplementary_unit_quantity.text = str(tariff_data.get('qty'))
            else:
                # supplementary_unit_quantity_null = ET.SubElement(supplementary_unit_quantity, 'null')
                supplementary_unit_quantity.text=""

        # Add the Valuation_method_code sub-element under Tarification
        valuation_method_code = ET.SubElement(tarification, 'Valuation_method_code')
        # valuation_method_code_null = ET.SubElement(valuation_method_code, 'null')
        valuation_method_code.text = ""

        # Add the A.I._code sub-element under Tarification
        ai_code = ET.SubElement(tarification, 'A.I._code')
        ai_code_null = ET.SubElement(ai_code, 'null')

        # Add Goods_description element
        goods_description = ET.SubElement(item_element, "Goods_description")
        # Add child elements under Goods_description
        ET.SubElement(goods_description, "Country_of_origin_code").text = ""
        ET.SubElement(goods_description, "Country_of_origin_region").text = ""
        ET.SubElement(goods_description, "Description_of_goods").text = ""
        ET.SubElement(goods_description, "Commercial_Description").text = ""

        # Add Previous_doc element
        previous_doc = ET.SubElement(item_element, "Previous_doc")
        # Add child elements under Previous_doc
        ET.SubElement(previous_doc, "Summary_declaration").text = "<null/>"
        ET.SubElement(previous_doc, "Summary_declaration_sl").text = "<null/>"
        ET.SubElement(previous_doc, "Previous_document_reference").text = "<null/>"
        ET.SubElement(previous_doc, "Previous_warehouse_code").text = "<null/>"

        # Add Licence_number element
        licence_number = ET.SubElement(item_element, "Licence_number")
        licence_number.text = "<null/>"

        # Add Amount_deducted_from_licence element
        amount_deducted_from_licence = ET.SubElement(item_element, "Amount_deducted_from_licence")
        amount_deducted_from_licence.text = ""

        # Add Quantity_deducted_from_licence element
        quantity_deducted_from_licence = ET.SubElement(item_element, "Quantity_deducted_from_licence")
        quantity_deducted_from_licence.text = ""

        # Add Free_text_1 element
        free_text_1 = ET.SubElement(item_element, "Free_text_1")
        free_text_1.text = "<null/>"

        # Add Free_text_2 element
        free_text_2 = ET.SubElement(item_element, "Free_text_2")
        free_text_2.text = "<null/>"

        # Add the Taxation sub-element under the Item element
        taxation = ET.SubElement(item_element, 'Taxation')

        # Add the Item_taxes_amount sub-element under Taxation
        item_taxes_amount = ET.SubElement(taxation, 'Item_taxes_amount')
        item_taxes_amount.text = '1.5'

        # Add the Item_taxes_guaranted_amount sub-element under Taxation
        item_taxes_guaranteed_amount = ET.SubElement(taxation, 'Item_taxes_guaranted_amount')

        # Add the Item_taxes_mode_of_payment sub-element under Taxation
        item_taxes_mode_of_payment = ET.SubElement(taxation, 'Item_taxes_mode_of_payment')
        item_taxes_mode_of_payment.text = '1'

        # Add the Counter_of_normal_mode_of_payment sub-element under Taxation
        counter_of_normal_mode_of_payment = ET.SubElement(taxation, 'Counter_of_normal_mode_of_payment')

        # Add the Displayed_item_taxes_amount sub-element under Taxation
        displayed_item_taxes_amount = ET.SubElement(taxation, 'Displayed_item_taxes_amount')

        # Add the Taxation_line sub-element under Taxation
        taxation_line = ET.SubElement(taxation, 'Taxation_line')

        # Add the Duty_tax_code sub-element under Taxation_line
        duty_tax_code = ET.SubElement(taxation_line, 'Duty_tax_code')
        duty_tax_code.text = 'STD'

        # Add the Duty_tax_Base sub-element under Taxation_line
        duty_tax_base = ET.SubElement(taxation_line, 'Duty_tax_Base')
        duty_tax_base.text = '0.00'

        # Add the Duty_tax_rate sub-element under Taxation_line
        duty_tax_rate = ET.SubElement(taxation_line, 'Duty_tax_rate')
        duty_tax_rate.text = '0.0'

        # Add the Duty_tax_amount sub-element under Taxation_line
        duty_tax_amount = ET.SubElement(taxation_line, 'Duty_tax_amount')
        duty_tax_amount.text = '1.50'

        # Add the Duty_tax_MP sub-element under Taxation_line
        duty_tax_mp = ET.SubElement(taxation_line, 'Duty_tax_MP')
        duty_tax_mp.text = '1'

        # Add the Duty_tax_Type_of_calculation sub-element under Taxation_line
        duty_tax_type_of_calculation = ET.SubElement(taxation_line, 'Duty_tax_Type_of_calculation')
        duty_tax_type_of_calculation_null = ET.SubElement(duty_tax_type_of_calculation, 'null')

        for k in range(7):
            # Add the Taxation_line sub-element under Taxation
            taxation_line = ET.SubElement(taxation, 'Taxation_line')

            # Add the Duty_tax_code sub-element under Taxation_line
            duty_tax_code = ET.SubElement(taxation_line, 'Duty_tax_code')
            duty_tax_code_null = ET.SubElement(duty_tax_code, 'null')

            # Add the Duty_tax_Base sub-element under Taxation_line
            duty_tax_base = ET.SubElement(taxation_line, 'Duty_tax_Base')

            # Add the Duty_tax_rate sub-element under Taxation_line
            duty_tax_rate = ET.SubElement(taxation_line, 'Duty_tax_rate')

            # Add the Duty_tax_amount sub-element under Taxation_line
            duty_tax_amount = ET.SubElement(taxation_line, 'Duty_tax_amount')

            # Add the Duty_tax_MP sub-element under Taxation_line
            duty_tax_mp = ET.SubElement(taxation_line, 'Duty_tax_MP')
            duty_tax_mp_null = ET.SubElement(duty_tax_mp, 'null')

            # Add the Duty_tax_Type_of_calculation sub-element under Taxation_line
            duty_tax_type_of_calculation = ET.SubElement(taxation_line, 'Duty_tax_Type_of_calculation')
            duty_tax_type_of_calculation_null = ET.SubElement(duty_tax_type_of_calculation, 'null')

        # Add the Valuation_item sub-element under Item
        valuation_item = ET.SubElement(item_element, 'Valuation_item')

        # Add Weight_itm sub-element under Valuation_item
        weight_itm = ET.SubElement(valuation_item, 'Weight_itm')
        gross_weight_itm = ET.SubElement(weight_itm, 'Gross_weight_itm')
        gross_weight_itm.text = str(round(unit_weight*tariff_data.get('qty'),2))
        net_weight_itm = ET.SubElement(weight_itm, 'Net_weight_itm')
        net_weight_itm.text = str(round(unit_weight*tariff_data.get('qty'),2))

        # Add Total_cost_itm sub-element under Valuation_item
        total_cost_itm = ET.SubElement(valuation_item, 'Total_cost_itm')
        total_cost_itm.text = str(tariff_data.get('base_amount'))

        # Add Total_CIF_itm sub-element under Valuation_item
        total_cif_itm = ET.SubElement(valuation_item, 'Total_CIF_itm')
        total_cif_itm.text = str(tariff_data.get('amount'))

        # Add Rate_of_adjustement sub-element under Valuation_item
        rate_of_adjustment = ET.SubElement(valuation_item, 'Rate_of_adjustement')

        # Add Statistical_value sub-element under Valuation_item
        statistical_value = ET.SubElement(valuation_item, 'Statistical_value')
        statistical_value.text = ''

        # Add Alpha_coeficient_of_apportionment sub-element under Valuation_item
        alpha_coeficient_of_apportionment = ET.SubElement(valuation_item, 'Alpha_coeficient_of_apportionment')
        alpha_coeficient_of_apportionment.text = '1.0'

        # Add Item_Invoice sub-element under Valuation_item
        item_invoice = ET.SubElement(valuation_item, 'Item_Invoice')
        amount_national_currency = ET.SubElement(item_invoice, 'Amount_national_currency')
        amount_national_currency.text = str(tariff_data.get('base_rate'))
        amount_foreign_currency = ET.SubElement(item_invoice, 'Amount_foreign_currency')
        amount_foreign_currency.text = str(tariff_data.get('rate'))
        currency_code = ET.SubElement(item_invoice, 'Currency_code')
        currency_code.text = sales.get("currency")
        currency_name = ET.SubElement(item_invoice, 'Currency_name')
        currency_name.text = 'No foreign currency'
        currency_rate = ET.SubElement(item_invoice, 'Currency_rate')
        currency_rate.text = str(sales.get('conversion_rate'))

        # Add item_external_freight sub-element under Valuation_item
        item_external_freight = ET.SubElement(valuation_item, 'item_external_freight')
        amount_national_currency = ET.SubElement(item_external_freight, 'Amount_national_currency')
        amount_national_currency.text = '0.0'
        amount_foreign_currency = ET.SubElement(item_external_freight, 'Amount_foreign_currency')
        amount_foreign_currency.text = '0.0'
        currency_code = ET.SubElement(item_external_freight, 'Currency_code')
        currency_name = ET.SubElement(item_external_freight, 'Currency_name')
        currency_name.text = 'No foreign currency'
        currency_rate = ET.SubElement(item_external_freight, 'Currency_rate')
        currency_rate.text = '0.0'

        # Add item_internal_freight sub-element under Valuation_item
        item_internal_freight = ET.SubElement(valuation_item, 'item_internal_freight')
        amount_national_currency = ET.SubElement(item_internal_freight, 'Amount_national_currency')
        amount_national_currency.text = '0.0'
        amount_foreign_currency = ET.SubElement(item_internal_freight, 'Amount_foreign_currency')
        amount_foreign_currency.text = '0.0'
        currency_code = ET.SubElement(item_internal_freight, 'Currency_code')
        # currency_code.text = 'USD'
        currency_name = ET.SubElement(item_internal_freight, 'Currency_name')
        currency_name.text = 'No foreign currency'
        currency_rate = ET.SubElement(item_internal_freight, 'Currency_rate')
        currency_rate.text = '0.0'

        # Add item_insurance sub-element under Valuation_item
        item_insurance = ET.SubElement(valuation_item, 'item_insurance')
        amount_national_currency = ET.SubElement(item_insurance, 'Amount_national_currency')
        amount_national_currency.text = '0.0'
        amount_foreign_currency = ET.SubElement(item_insurance, 'Amount_foreign_currency')
        amount_foreign_currency.text = '0.0'
        currency_code = ET.SubElement(item_insurance, 'Currency_code')
        currency_name = ET.SubElement(item_insurance, 'Currency_name')
        currency_name.text = 'No foreign currency'
        currency_rate = ET.SubElement(item_insurance, 'Currency_rate')
        currency_rate.text = '0.0'

        # Add item_other_cost sub-element under Valuation_item
        item_other_cost = ET.SubElement(valuation_item, 'item_other_cost')
        amount_national_currency = ET.SubElement(item_other_cost, 'Amount_national_currency')
        amount_national_currency.text = '0.0'
        amount_foreign_currency = ET.SubElement(item_other_cost, 'Amount_foreign_currency')
        amount_foreign_currency.text = '0.0'
        currency_code = ET.SubElement(item_other_cost, 'Currency_code')
        currency_name = ET.SubElement(item_other_cost, 'Currency_name')
        currency_name.text = 'No foreign currency'
        currency_rate = ET.SubElement(item_other_cost, 'Currency_rate')
        currency_rate.text = '0.0'

        # Add item_deduction sub-element under Valuation_item
        item_deduction = ET.SubElement(valuation_item, 'item_deduction')
        amount_national_currency = ET.SubElement(item_deduction, 'Amount_national_currency')
        amount_national_currency.text = '0.0'
        amount_foreign_currency = ET.SubElement(item_deduction, 'Amount_foreign_currency')
        amount_foreign_currency.text = '0.0'
        currency_code = ET.SubElement(item_deduction, 'Currency_code')
        currency_name = ET.SubElement(item_deduction, 'Currency_name')
        currency_name.text = 'No foreign currency'
        currency_rate = ET.SubElement(item_deduction, 'Currency_rate')
        currency_rate.text = '0.0'

        # Add Market_valuer sub-element under Valuation_item
        market_valuer = ET.SubElement(valuation_item, 'Market_valuer')
        rate = ET.SubElement(market_valuer, 'Rate')
        currency_code = ET.SubElement(market_valuer, 'Currency_code')
        currency_code.text = '</null>'  # Assuming you want the value to be 'null'
        currency_amount = ET.SubElement(market_valuer, 'Currency_amount')
        basis_description = ET.SubElement(market_valuer, 'Basis_description')
        basis_description.text = '</null>'  # Assuming you want the value to be 'null'
        basis_amount = ET.SubElement(market_valuer, 'Basis_amount')

    vehicle_list = ET.SubElement(asycuda, 'Vehicle_List')


    #######################XML Generate######################## 
    b_xml =  minidom.parseString(ET.tostring(asycuda)).toprettyxml(indent="")
    # b_xml =  minidom.parseString(ET.tostring(asycuda)).toprettyxml(indent="\t")
    # b_xml =  minidom.parseString(ET.tostring(asycuda)).toprettyxml(indent="  ")

    # b_xml = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + xml
    # print("*************",b_xml)

    file_name = str(name)+".xml"
    frappe.local.response.filename = file_name
    frappe.local.response.filecontent = b_xml
    frappe.local.response.type = "download"
    # return "wassup"