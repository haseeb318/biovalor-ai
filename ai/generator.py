import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai import types

from ai.prompts import build_prompts


class MissingAPIKeyError(RuntimeError):
	"""Raised when the Gemini API key is not configured."""


class AIAnalysisError(RuntimeError):
	"""Raised when the Gemini request cannot be completed."""


def generate_analysis(scientific_context, user_context, score):
	"""Generate an analysis from one scientific record and the current score."""
	if scientific_context is None or (
		not isinstance(scientific_context, str)
		and not hasattr(scientific_context, "items")
	):
		raise ValueError("Scientific context is empty or invalid.")

	load_dotenv(override=True)
	api_key = os.getenv("GEMINI_API_KEY", "").strip()
	if not api_key or api_key == "your_gemini_api_key_here":
		raise MissingAPIKeyError(
			"Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file."
		)

	model = os.getenv("GEMINI_MODEL", "gemini-3.7-flash").strip() or "gemini-3.7-flash"
	system_prompt, user_prompt = build_prompts(
		scientific_context, user_context, score
	)

	try:
		client = genai.Client(api_key=api_key)
		for attempt in range(4):
			try:
				response = client.models.generate_content(
					model=model,
					contents=user_prompt,
					config=types.GenerateContentConfig(
						system_instruction=system_prompt,
					),
				)
				break
			except errors.ServerError as error:
				is_temporary_503 = (
					getattr(error, "status", None) == 503
					and "UNAVAILABLE" in str(error)
				)
				if not is_temporary_503 or attempt == 3:
					if is_temporary_503:
						raise AIAnalysisError(
							"Gemini is temporarily unavailable after 3 retries. "
							"Please try again later."
						) from error
					raise
				time.sleep(2 ** (attempt + 1))
		analysis = (response.text or "").strip()
	except Exception as error:
		if isinstance(error, AIAnalysisError):
			raise
		raise AIAnalysisError(str(error)) from error

	if not analysis:
		raise AIAnalysisError("Gemini returned an empty response.")

	return analysis