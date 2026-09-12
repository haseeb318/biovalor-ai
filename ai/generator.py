# """Gemini client integration for grounded analysis and follow-up answers."""

import os
import time
import json
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai import types

from ai.prompts import build_followup_prompt, build_prompts


logger = logging.getLogger(__name__)

# Signal that the local Gemini credential is unavailable.
class MissingAPIKeyError(RuntimeError):
	"""Raised when the Gemini API key is not configured."""


# Signal that Gemini could not complete an analysis request.
class AIAnalysisError(RuntimeError):
	"""Raised when the Gemini request cannot be completed."""


FALLBACK_MODELS = [
	"gemini-3.6-flash",
	"gemini-3.5-flash",
	"gemini-3.1-flash-lite",
]

# Identify retryable Gemini service-unavailable responses.
def _is_temporary_unavailable(error):
	return (
		isinstance(error, errors.APIError)
		and getattr(error, "code", None) == 503
		and str(getattr(error, "status", "")).upper() == "UNAVAILABLE"
		and "UNAVAILABLE" in str(error).upper()
	)

# Send one request with bounded retry behavior.
def _generate_with_model(
	client, model, system_prompt, user_prompt, retries, response_mime_type="application/json"
):
	for attempt in range(retries + 1):
		logger.info(
			"Attempting Gemini model %s (attempt %s/%s).",
			model,
			attempt + 1,
			retries + 1,
		)
		try:
			config_kwargs = {"system_instruction": system_prompt}
			if response_mime_type:
				config_kwargs["response_mime_type"] = response_mime_type
			chat = client.chats.create(
				model=model,
				config=types.GenerateContentConfig(**config_kwargs),
			)
			return chat.send_message(user_prompt)
		except errors.APIError as error:
			if not _is_temporary_unavailable(error):
				raise
			if attempt == retries:
				raise
			delay = 2 ** (attempt + 1)
			logger.warning(
				"Gemini model %s returned temporary 503; retrying in %s seconds.",
				model,
				delay,
			)
			time.sleep(delay)

# Try the configured model, then temporary-outage fallbacks.
def _generate_with_fallback(
	client, model, system_prompt, user_prompt, response_mime_type="application/json"
):
	try:
		return _generate_with_model(
			client,
			model,
			system_prompt,
			user_prompt,
			retries=3,
			response_mime_type=response_mime_type,
		)
	except errors.APIError as primary_error:
		if not _is_temporary_unavailable(primary_error):
			raise

		logger.warning(
			"Primary Gemini model %s exhausted retries; trying fallback models.",
			model,
		)
		for fallback_model in FALLBACK_MODELS:
			try:
				return _generate_with_model(
					client,
					fallback_model,
					system_prompt,
					user_prompt,
					retries=0,
					response_mime_type=response_mime_type,
				)
			except errors.APIError as fallback_error:
				if not _is_temporary_unavailable(fallback_error):
					raise
				logger.warning(
					"Fallback Gemini model %s returned temporary 503; trying the next model.",
					fallback_model,
				)

		raise AIAnalysisError(
			"Gemini is temporarily unavailable across all configured models. "
			"Please try again later."
		) from primary_error

# Generate one grounded structured recommendation.
def generate_analysis(scientific_context, user_context, score):
	if scientific_context is None or (
		not isinstance(scientific_context, str)
		and not hasattr(scientific_context, "items")
	):
		raise ValueError("Scientific context is empty or invalid.")

	load_dotenv()
	api_key = os.getenv("GEMINI_API_KEY", "").strip()
	if not api_key or api_key == "your_gemini_api_key_here":
		raise MissingAPIKeyError(
			"Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file."
		)

	model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"
	system_prompt, user_prompt = build_prompts(
		scientific_context, user_context, score
	)

	try:
		client = genai.Client(api_key=api_key)
		response = _generate_with_fallback(
			client, model, system_prompt, user_prompt
		)
		analysis_text = (response.text or "").strip()
	except Exception as error:
		if isinstance(error, AIAnalysisError):
			raise
		raise AIAnalysisError(str(error)) from error

	if not analysis_text:
		raise AIAnalysisError("Gemini returned an empty response.")

	try:
		analysis = json.loads(analysis_text)
	except json.JSONDecodeError as error:
		raise AIAnalysisError(
			"Gemini returned invalid JSON instead of the required structured response."
		) from error

	if not isinstance(analysis, dict):
		raise AIAnalysisError("Gemini returned JSON that was not an object.")

	return analysis

# Generate one grounded answer to a follow-up question.
def ask_followup_question(
	scientific_context, user_context, score, analysis, question
):
	if not isinstance(question, str) or not question.strip():
		raise ValueError("Please enter a question.")
	if not hasattr(scientific_context, "items") or not isinstance(analysis, dict):
		raise ValueError("The analysis context is invalid.")

	load_dotenv()
	api_key = os.getenv("GEMINI_API_KEY", "").strip()
	if not api_key or api_key == "your_gemini_api_key_here":
		raise MissingAPIKeyError(
			"Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file."
		)

	model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"
	system_prompt, user_prompt = build_followup_prompt(
		scientific_context, user_context, score, analysis, question.strip()
	)

	try:
		client = genai.Client(api_key=api_key)
		response = _generate_with_fallback(
			client,
			model,
			system_prompt,
			user_prompt,
			response_mime_type=None,
		)
		answer = (response.text or "").strip()
	except Exception as error:
		if isinstance(error, AIAnalysisError):
			raise
		raise AIAnalysisError(
			"Gemini could not answer the follow-up question. Please try again later."
		) from error

	if not answer:
		raise AIAnalysisError("Gemini returned an empty response.")
	return answer
