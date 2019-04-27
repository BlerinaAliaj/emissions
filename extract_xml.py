import xml.etree.ElementTree as ET
from sqlalchemy import func
from model import Company, Report, Emissions, connect_to_db, db
from server import app
import glob

companies = []
reports = []


def scan_files():
	# Function that reads all files in the directory that end in .xml

	files = glob.glob('./emissions/*.xml')
	#files = glob.glob('Emissions_Report (58).xml')
	for file in files:
		print(file)
		extract_info(file)


def extract_info(file):
	# Function that extracts all data and cleans it up
	parser = ET.XMLParser(encoding="utf-8")
	tree = ET.parse(file)
	root = tree.getroot()

	# Attributes of root are nested in an object. 
	# root.tag gives the name of the tag, in this case the tag of <Report> is the Name or as it is written below.
	# root.tag is the same as root.attrib['Name']
	root_name = root.attrib['Name'] 
	year = root.attrib['Textbox4'].strip().split(' ')[-1]

	# Extract data on company by looking at the Details_Collection
	for detail in root.findall(".//{Emissions_Report}Details_Collection"):
		extract_company_info(detail)
		extract_report_info(detail, year, root)


def extract_company_info(detail):
	# Function that extracts company data

	info = detail[0].attrib
	name_of_company = info['EntityName1'].strip()
	industry = info['Textbox29']
	address = info['Textbox41']
	website = info['EntityURL3'].split(':')[-1].strip()

	# Write info to the company list
	company = {'name': name_of_company,
			   'industry': industry,
			   'address': address,
			   'website': website }
	companies.append(company)


def extract_report_info(detail, year, root):
	# Function that extracts report information

	report_scopes = []

	info = detail[0].attrib
	name_of_company = info['EntityName1'].strip()
	verification_body = info['Textbox108'].split(':')[-1].strip()
	level_of_assur = info['limitedassurace'].split(':')[-1].strip()
	gwp_stand = info['Textbox2'].split(':')[-1].strip()
	reporting_protocol = info['Textbox73'].split(':')[-1].strip()
	report_scopes = [] # scope 1, 2, 3  with totals and name , tables

	# Extract data for total emissions of C02 by entity
	for elem in root.findall(".//{Emissions_Report}CO2e_SubReport"):
		# Report description is under <Report Name=""> which is first sub-elem in list:
		rep_name = elem[0].attrib['Name'] # Emissions_Report_CO2eGas
		rep_description = elem[0].attrib['Textbox21'] # We neet to check for '| Total in metric tons of CO2e'
		# This will give a list of all table elements and children of those tables
		scopes = []

		tables = elem.findall('.//{Emissions_Report}table1')
		for table in tables:
			# For each table, create a child instance with name, id, etc...
			table_name = table.attrib['textbox2'].strip()
			table_id = "".join(table_name.strip().split(' '))
			table_scope = table_name.split('-')[0].strip()
			scope_net = table.get('TOTALCO2e', 0)
			# the total for the particular table is under <Groups Textbox25..>
			# Loop below recursively untill find elem.tag == "Groups"
			scope_total = find_total(table, '{Emissions_Report}Groups')
			
			# Find all children for that given table/ these are the individual emissions
			activities = find_children(table)
			scope_offsets = 0
			for activity in activities:
				if activity['category'] == 'Applied Offsets':
					scope_offsets = activity['total_co2e']
			# Write a scope object for each table in our .xml file
			scope = {'name': table_name,
					 'scope_id': table_id,
					 'scope': table_scope,
					 'scope_net': scope_net,
					 'scope_total': scope_total,
					 'scope_offsets': scope_offsets,
					 'activities': activities
			}

			# Check to see if there are dublicates, if there are, remove previous ones. Last entry wins.
			
			i = 0
			while i < len(scopes):
				if scopes[i]['scope_id'] == scope['scope_id']:
					scopes.pop(i)
				else:
					i += 1
			scopes.append(scope)

		#Add all the tables to the reports list. 
		report_scopes += scopes

	#Write the items to the global report list
	report = { 'name': name_of_company,
			   'year': year,
			   'verification_body': verification_body,
			   'level_of_assur': level_of_assur,
			   'gwp_stand': gwp_stand,
			   'reporting_protocol': reporting_protocol,
			   'scopes': report_scopes}
	
	reports.append(report)
	

def find_total(table, s):
	# Function to find total emissions for table/category
	my_input = [table]

	while len(my_input) > 0:
		var = my_input.pop()
		if var.tag == s:
			return var.get('Textbox25', 0)
		else:
			my_input.append(var[0])




def find_children(table):
	# Finds all children for a given table
	children = []
	my_input = [table]
	while len(my_input) > 0:
		var = my_input.pop(0)

		if var.tag == '{Emissions_Report}Detail':
			category = var.attrib['Activity']
			total_co2e = var.get('TOTALCO2e1', 0)
			co2_co2e = var.get('CO2', 0)
			#co2_co2e = var.attrib['CO2']
			ch4_co2e = var.get('CH4', 0)
			n2o_co2e = var.get('N2O1', 0)
			hfc_co2e = var.get('HFC_CO2e1', 0)
			pfc_co2e = var.get('PFC_CO2e1', 0)
			nf3_co2e = var.get('NF31', 0)
			sf6_co2e = var.get('SF61', 0)

			child = { 'category': category,
					  'total_co2e': total_co2e,
					  'co2_co2e': co2_co2e,
					  'ch4_co2e': ch4_co2e,
					  'n2o_co2e': n2o_co2e,
					  'hfc_co2e': hfc_co2e,
					  'pfc_co2e': pfc_co2e,
					  'nf3_co2e': nf3_co2e,
					  'sf6_co2e': sf6_co2e }

			children.append(child)

		else:
			for e in var:
				my_input.append(e)

	return children


def populate_company_table():
	# Function that populates company table from company list

	# Clear out all previous tables
	Company.query.delete()
	db.session.commit()

	for comp in companies:
		name_of_company = comp['name']
		industry = comp['industry']
		address = comp['address']
		website = comp['website']

		#Add Company ifo to the database
		company = Company(name=name_of_company, industry=industry, address=address, website=website)
		db.session.add(company)
		db.session.commit()


def populate_report_table():
	# Will read from report list, if items are missing we will replace with items below after analysis

	# Deletes all table rows to assure no dublicates
	Report.query.delete()
	db.session.commit()

	scope1_total = 0
	scope1_net = 0
	scope1_offsets = 0
	scope3_total = 0
	scope3_net = 0
	scope3_offsets = 0

	scope2_market_total = 0
	scope2_market_net = 0
	scope2_market_offsets = 0
	scope2_location_total = 0
	scope2_location_net = 0
	scope2_location_offsets = 0

	for report in reports:
		name_of_company = report['name']
		year = report['year']
		co_id = Company.query.filter_by(name=name_of_company).first().co_id
		verification_body = report['verification_body']
		level_of_assur = report['level_of_assur']
		gwp_stand = report['gwp_stand']
		reporting_protocol = report['reporting_protocol']

		for scope in report['scopes']:
			if scope['scope'] == 'Scope 1':
				scope1_total = scope['scope_total']
				scope1_net = scope['scope_net']
				scope1_offsets = scope['scope_offsets']

			elif scope['scope'] == 'Optional':
				scope3_total = scope['scope_total']
				scope3_net = scope['scope_net']
				scope3_offsets = scope['scope_offsets'] 
			else:
				if "Market" in scope['name']:
					scope2_market_total = scope['scope_total']
					scope2_market_net = scope['scope_net']
					scope2_market_offsets = scope['scope_offsets']
				elif "Location" in scope['name']:
					scope2_location_total = scope['scope_total']
					scope2_location_net = scope['scope_net']
					scope2_location_offsets = scope['scope_offsets']


		rep = Report(year=year, co_id=co_id, verification_body=verification_body, level_assurance=level_of_assur,
						gwp_standard=gwp_stand, rep_protocol=reporting_protocol, scope1_total=scope1_total, scope1_net=scope1_net,
						scope1_offsets=scope1_offsets, scope2_market_total=scope2_market_total, scope2_market_net=scope2_market_net,
						scope2_market_offsets=scope2_market_offsets, scope2_location_total=scope2_location_total, 
						scope2_location_net=scope2_location_net, scope2_location_offsets=scope2_location_offsets,
						scope3_total=scope3_total, scope3_net=scope3_net, scope3_offsets=scope3_offsets)

		db.session.add(rep)
		db.session.commit()


def populate_emissions():
	# Function to populate emissions table

	# Delete all table rows to insure no dublicates
	Emissions.query.delete()
	db.session.commit()


	for report in reports:
		year = report['year']
		name_of_company = report['name']
		co_id = Company.query.filter_by(name=name_of_company).first().co_id
		report_id = Report.query.filter_by(year=year, co_id=co_id).first().report_id

		for scope in report['scopes']:
			emiss_scope = scope['scope']
			for activity in scope['activities']:
				category = activity['category']
				total_co2e = activity['total_co2e']
				co2_co2e = activity['co2_co2e']
				ch4_co2e = activity['ch4_co2e']
				n2o_co2e = activity['n2o_co2e']
				hfc_co2e = activity['hfc_co2e']
				pfc_co2e = activity['pfc_co2e']
				nf3_co2e = activity['nf3_co2e']
				sf6_co2e = activity['sf6_co2e']

				emissions = Emissions(report_id=report_id, scope=emiss_scope, category=category,
									  total_co2e=total_co2e, co2_co2e=co2_co2e, ch4_co2e=ch4_co2e,
									  n2o_co2e=n2o_co2e, hfc_co2e=hfc_co2e, pfc_co2e=pfc_co2e,
									  nf3_co2e=nf3_co2e, sf6_co2e=sf6_co2e)
				db.session.add(emissions)
				db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Run functions to extract data
    scan_files()
    # Run functions to write to db
    populate_company_table()
    populate_report_table()
    populate_emissions()



 