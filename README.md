# BioValor AI

BioValor AI is a Streamlit-based Generative AI decision-support application for identifying and comparing potential valorization pathways for biological waste.

## Current Features

- Waste profile input for material type, quantity, source, and condition
- Curated CSV scientific knowledge base
- Transparent Valorization Suitability Score out of 100
- Gemini-powered evidence-grounded recommendation generation
- Structured AI output for components, pathways, processing, applications, and limitations
- AI response validation before results are displayed
- Scientific evidence panel with sources, DOI values, links, and evidence level
- Follow-up questions about the generated analysis
- Pathway comparison support for recommended and alternative pathways
- Responsive Home and About pages with persistent Streamlit session state

## Technology Stack

- Python
- Streamlit
- Pandas
- python-dotenv
- Google Gemini Generative AI
- CSV knowledge base

## Project Structure

```text
biovalor-ai/
├── app.py                  # Streamlit user interface
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── data/
│   └── waste_knowledge.csv # Scientific knowledge base
├── ai/
│   ├── generator.py        # Gemini requests and fallback handling
│   └── prompts.py          # Grounded prompt construction
└── utils/
    ├── comparison.py       # Pathway comparison helpers
    ├── data_loader.py      # CSV record loading
    ├── scoring.py          # Transparent suitability scoring
    └── validation.py       # Structured AI response validation
```

## Environment Setup

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure Gemini

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your Google Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.7-flash
```

Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Never commit `.env` or expose the API key publicly. The app can open without a key, but AI analysis and follow-up questions require `GEMINI_API_KEY`.

## Run the Application

From the project directory:

```powershell
.venv\Scripts\activate
streamlit run app.py
```

Open the local URL shown by Streamlit, normally:

```text
http://localhost:8501
```

## How It Works

1. Select a biological waste stream and enter its quantity, source, and condition.
2. BioValor AI retrieves the matching scientific record from the CSV knowledge base.
3. The scoring engine calculates a transparent suitability score.
4. Gemini receives only the selected scientific context and user input.
5. The generated response is validated against the required structured schema.
6. The dashboard displays the recommendation, score, processing pathway, applications, limitations, and scientific evidence.
7. Users can ask a grounded follow-up question about the displayed analysis.

## Navigation and State

Streamlit reruns the script when the user navigates between Home and About. This is normal Streamlit behavior. Analysis results are stored in `st.session_state` so they can remain available during the current browser session.

## Important Limitations

The Valorization Suitability Score is a transparent prototype decision-support score. It is not a probability of success, experimental yield prediction, economic guarantee, or industrial recommendation. AI-generated interpretations should be reviewed against the displayed scientific sources.

## Development Status

The project currently includes the core prototype workflow. Future work may include expanded knowledge-base coverage, broader pathway comparison, testing, deployment, and additional validation.
