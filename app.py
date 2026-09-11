import streamlit as st
import pandas as pd

from ai.generator import AIAnalysisError, MissingAPIKeyError, generate_analysis
from utils.data_loader import get_waste_data
from utils.scoring import calculate_valorization_score


SUPPORTED_WASTES = [
	"Eggshell",
	"Fish scales",
	"Chicken feathers",
	"Rice husk",
	"Banana peel",
	"Sugarcane bagasse",
	"Citrus/fruit peels",
	"Spent coffee grounds",
	"Shrimp shells",
	"Sawdust / wood-processing residue",
]


def display_ai_analysis(analysis):
	"""Render a structured AI response safely for the Streamlit dashboard."""
	def text_value(field_name):
		value = analysis.get(field_name)
		return str(value).strip() if value not in (None, "") else "Not available"

	def list_value(field_name):
		value = analysis.get(field_name)
		if not value:
			return []
		if isinstance(value, str):
			return [value]
		return [str(item).strip() for item in value if str(item).strip()]

	primary_column, pathway_column = st.columns(2)
	with primary_column:
		st.subheader("Primary Component")
		st.info(text_value("primary_component"))
	with pathway_column:
		st.subheader("Recommended Valorization Pathway")
		st.success(text_value("recommended_pathway"))

	st.subheader("Why This Pathway?")
	st.write(text_value("reason"))

	st.subheader("Processing Pathway")
	processing_steps = list_value("processing_steps")
	if processing_steps:
		for step_number, step in enumerate(processing_steps, start=1):
			st.markdown(f"{step_number}. {step}")
	else:
		st.info("Processing steps are not available.")

	st.subheader("Alternative Pathways")
	alternative_pathways = list_value("alternative_pathways")
	if alternative_pathways:
		for pathway in alternative_pathways:
			st.markdown(f"- {pathway}")
	else:
		st.info("Alternative pathways are not available.")

	st.subheader("Potential Applications")
	applications = list_value("applications")
	if applications:
		for application in applications:
			st.markdown(f"- {application}")
	else:
		st.info("Potential applications are not available.")

	st.subheader("Limitations")
	limitations = list_value("limitations")
	if limitations:
		for limitation in limitations:
			st.warning(limitation)
	else:
		st.info("Limitations are not available.")

	st.subheader("Evidence Level")
	st.info(text_value("evidence_level"))


def display_scientific_evidence(waste_record):
	"""Render authoritative evidence details from the selected knowledge-base record."""
	def record_value(field_name):
		value = waste_record.get(field_name)
		if value is None or pd.isna(value) or not str(value).strip():
			return "Not available"
		return str(value).strip()

	st.subheader("Scientific Evidence")
	evidence_level = record_value("evidence_level")
	source_title = record_value("source_title")
	doi = record_value("doi")
	source_url = record_value("source_url")

	evidence_column, source_column = st.columns(2)
	with evidence_column:
		st.markdown("**Evidence Level**")
		st.info(evidence_level)
	with source_column:
		st.markdown("**Source**")
		st.write(source_title)

	st.markdown("**DOI**")
	st.write(doi)
	if source_url == "Not available":
		st.markdown("**Reference / View scientific source**")
		st.write("Not available")
	else:
		st.markdown(f"**Reference / View scientific source:** [{source_url}]({source_url})")


st.title("BioValor AI")
st.write("Transform biological waste into potential valuable resources.")

selected_waste = st.selectbox("Waste type", SUPPORTED_WASTES)
quantity = st.number_input("Quantity", min_value=None, value=0.0, step=1.0, format="%.2f")
source = st.selectbox(
	"Source",
	[
		"Food processing",
		"Poultry processing",
		"Fish processing",
		"Seafood processing",
		"Agricultural residue",
		"Household food waste",
		"Coffee brewing/processing",
		"Forestry/wood processing",
		"Other",
	],
)
condition = st.selectbox("Condition", ["Wet", "Dry", "Mixed", "Unknown"])

if st.button("ANALYZE WITH AI"):
	if quantity <= 0:
		st.error("Please enter a valid quantity greater than 0 kg.")
	else:
		try:
			waste_record = get_waste_data(selected_waste)
		except (FileNotFoundError, RuntimeError) as error:
			st.error(str(error))
		else:
			st.subheader("Analysis input")
			st.write(f"Selected waste: {selected_waste}")
			st.write(f"Quantity: {quantity:g} kg")
			st.write(f"Source: {source}")
			st.write(f"Condition: {condition}")

			if waste_record is None:
				st.warning("This waste type is outside the current BioValor AI knowledge base.")
			else:
				st.success("Scientific information found: YES")
				score = calculate_valorization_score(waste_record)
				st.subheader("Valorization Suitability Score")
				st.write(f"{score['total_score']} / 100")
				st.write(f"Evidence strength: {score['evidence_strength']} / 25")
				st.write(f"Component value: {score['component_value']} / 25")
				st.write(f"Application potential: {score['application_potential']} / 20")
				st.write(f"Processing feasibility: {score['processing_feasibility']} / 15")
				st.write(f"Pathway maturity: {score['pathway_maturity']} / 15")
				st.caption("Prototype decision-support score")
				display_scientific_evidence(waste_record)

				try:
					analysis = generate_analysis(
						waste_record,
						{
							"waste_type": selected_waste,
							"quantity": f"{quantity:g}",
							"source": source,
							"condition": condition,
						},
						score,
					)
				except MissingAPIKeyError as error:
					st.warning(str(error))
				except (AIAnalysisError, ValueError) as error:
					st.error(f"AI analysis failed: {error}")
				else:
					st.subheader("AI-generated analysis")
					display_ai_analysis(analysis)

with st.expander("How is this score calculated?"):
	st.write(
		"Evidence strength — 25 points: based on the evidence level in the "
		"scientific knowledge base."
	)
	st.write(
		"Component value — 25 points: based on documented major components "
		"and valorization potential."
	)
	st.write(
		"Application potential — 20 points: based on documented products "
		"and applications."
	)
	st.write(
		"Processing feasibility — 15 points: based on documented processing "
		"complexity and limitations."
	)
	st.write(
		"Pathway maturity — 15 points: based on the documented pathway and "
		"evidence."
	)
