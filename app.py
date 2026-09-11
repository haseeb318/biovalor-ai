import streamlit as st

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
					st.write(analysis)

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
