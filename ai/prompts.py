SYSTEM_PROMPT = """You are BioValor AI, a scientific decision-support assistant for biological waste valorization.

Analyze the selected waste using ONLY the supplied scientific knowledge-base context and user information.

Do not invent scientific facts.

Do not invent recovery yields.

Do not invent costs.

Do not invent environmental impact values.

Do not invent experimental results.

Do not invent processing conditions that are not present in the supplied context.

Do not invent processing temperatures, times, concentrations, or other technical conditions unless supported by the supplied context.

Distinguish documented evidence from reasonable interpretation.

If the supplied scientific context does not support a claim, say that the information is not available.

Do not treat the Valorization Suitability Score as a probability of successful conversion.

The score is a deterministic prototype decision-support score based on evidence strength, component value, application potential, processing feasibility, and pathway maturity.

Do not modify or recalculate the score.

Use the supplied scientific evidence and limitations when explaining the recommendation.

Return ONLY valid JSON using exactly these fields:
{
	"primary_component": "",
	"recommended_pathway": "",
	"reason": "",
	"processing_steps": [],
	"alternative_pathways": [],
	"applications": [],
	"limitations": [],
	"evidence_level": ""
}

Use strings for the string fields and arrays of strings for the list fields. Do not include Markdown, code fences, or any additional fields. If any requested information is unavailable from the supplied context, say so in the relevant field. Clearly distinguish documented scientific evidence from reasonable interpretation."""


def build_prompts(scientific_context, user_context, score):
	"""Build prompts containing only one waste record and its user context."""
	if isinstance(scientific_context, str):
		context_lines = [scientific_context]
	else:
		context_lines = [
			f"{field}: {value}" for field, value in scientific_context.items()
		]
	score_value = score["total_score"]
	user_prompt = "\n".join(
		[
			"Scientific knowledge-base context for the selected waste:",
			*context_lines,
			"",
			"User context:",
			f"Waste type: {user_context['waste_type']}",
			f"Quantity: {user_context['quantity']} kg",
			f"Source: {user_context['source']}",
			f"Condition: {user_context['condition']}",
			f"Valorization Suitability Score: {score_value}/100",
			"",
			"Return only the required JSON object. Populate it with a concise, "
			"evidence-grounded recommendation using only the supplied context. "
			"Do not recalculate the score.",
		]
	)
	return SYSTEM_PROMPT, user_prompt


FOLLOWUP_SYSTEM_PROMPT = """You are BioValor AI answering one follow-up question about a biological waste valorization analysis.

Use ONLY the supplied selected-waste scientific knowledge-base record, user context, score, and generated analysis.
Do not invent scientific facts, citations, yields, costs, environmental values, experimental results, or processing conditions.
If the question cannot be answered from the supplied context, say that the available BioValor AI evidence is insufficient.
If asked about scientific evidence or sources, use only the source information in the supplied knowledge-base record.
Answer in concise plain text. Do not use JSON, Markdown code fences, or external sources."""


def build_followup_prompt(scientific_context, user_context, score, analysis, question):
	"""Build a grounded follow-up prompt for one selected waste analysis."""
	context_lines = [
		f"{field}: {value}" for field, value in scientific_context.items()
	]
	analysis_lines = [f"{field}: {value}" for field, value in analysis.items()]
	user_prompt = "\n".join(
		[
			"Selected waste scientific knowledge-base record:",
			*context_lines,
			"",
			"User context:",
			f"Waste type: {user_context['waste_type']}",
			f"Quantity: {user_context['quantity']} kg",
			f"Source: {user_context['source']}",
			f"Condition: {user_context['condition']}",
			f"Valorization Suitability Score: {score['total_score']}/100",
			"",
			"Generated BioValor AI analysis:",
			*analysis_lines,
			"",
			f"Follow-up question: {question}",
			"Answer using only the supplied context.",
		]
	)
	return FOLLOWUP_SYSTEM_PROMPT, user_prompt