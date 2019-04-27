# Company Table
# Report table, Table id, year, company, verification body, level of assurance etc... look up what will be added to this
# Emission table , emission id, linked to a report id, scope, type(emission or offset), description(subcategory, heating ,electricity, offsets), CO2 (and all gases). 


"""Models and database functions for Emissions Demo."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

##############################################################################
# Model definitions

class Company(db.Model):

	__tablename__ = "company"

	co_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
	name = db.Column(db.String(150), nullable=False)
	industry = db.Column(db.String(150), nullable=False)
	address = db.Column(db.String(300), nullable=False)
	website = db.Column(db.String(200), nullable=True)


	def __repr__(self):
		return "<Comany co_id={self.co_id} name={self.name} industry={self.industry}>"


class Report(db.Model):

	__tablename__ = "report"

	report_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
	year = db.Column(db.String(64), nullable=False)
	co_id = db.Column(db.Integer, db.ForeignKey('company.co_id', onupdate="CASCADE", ondelete="CASCADE"))
	verification_body = db.Column(db.String(150), nullable=True)
	level_assurance = db.Column(db.String(64), nullable=False)
	gwp_standard = db.Column(db.String(64), nullable=False)
	rep_protocol = db.Column(db.String(300), nullable=True)
	# Total Scope 1 emissions. 
	scope1_total = db.Column(db.Float, nullable=False)
	scope1_net = db.Column(db.Float, nullable=False)
	scope1_offsets = db.Column(db.Float, nullable=True)
	# Total Scope 2 Emissions. Scope 2 Has two versions to it. scope2 regional and scope2 market based. 
	scope2_market_total = db.Column(db.Float, nullable=True)
	scope2_market_net = db.Column(db.Float, nullable=True)
	scope2_market_offsets = db.Column(db.Float, nullable=True)

	scope2_location_total = db.Column(db.Float, nullable=True)
	scope2_location_net = db.Column(db.Float, nullable=True)
	scope2_location_offsets = db.Column(db.Float, nullable=True)

	scope3_total = db.Column(db.Float, nullable=True)
	scope3_net = db.Column(db.Float, nullable=True)
	scope3_offsets = db.Column(db.Float, nullable=True)

	


	def __repr__(self):
		return "<Report report_id={self.report_id} year={self.year} company_id={self.co_id}>"



class Emissions(db.Model):

	__tablename__ = "emissions"

	emissions_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
	report_id = db.Column(db.Integer, db.ForeignKey('report.report_id', onupdate="CASCADE", ondelete="CASCADE"))
	# Scope is string, it will be Scope 1 Direct Emissions, Scope2 Location Based Indirect Emission, 
	# Scope2 Market Based Indirect Emissions, Scope 3 Optional
	scope = db.Column(db.String(64), nullable=False)
	# Category is Fugitive, Purchased Electricity location/market, Purchased Heating location/market,
	# Business Travel, Employee Commuting --> Scope 3, offsets
	category = db.Column(db.String(150), nullable=False)
	# Gases
	total_co2e = db.Column(db.Float, nullable=False)
	co2_co2e = db.Column(db.Float, nullable=False)
	ch4_co2e = db.Column(db.Float, nullable=False)
	n2o_co2e = db.Column(db.Float, nullable=False)
	hfc_co2e = db.Column(db.Float, nullable=False)
	pfc_co2e = db.Column(db.Float, nullable=False)
	nf3_co2e = db.Column(db.Float, nullable=False)
	sf6_co2e = db.Column(db.Float, nullable=False)
	

	def __repr__(self):
		return "<Emissions emissions_id={self.emissions_id} report_id={self.report_id} scope={self.scope} category={self.category} total_co2e={self.total_co2e} >"




##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///emissions'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print("Connected to DB.")















