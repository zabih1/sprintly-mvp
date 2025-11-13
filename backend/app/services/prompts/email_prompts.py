"""Prompts for warm introduction email generation."""

FORMAL_EMAIL_PROMPT = """You are writing a professional, warm introduction email to connect a founder with an investor.

Context:
- Founder: {founder_name} from {founder_company} ({founder_position})
- Investor: {investor_name} from {investor_company} ({investor_position})
- Mutual Connection: {mutual_connection_name} ({mutual_connection_role})
- Match Score: {match_score}/100

Key Match Reasons:
{match_reasons}

Investment Fit:
- Sector: {sector_fit}
- Stage: {stage_fit}
- Geography: {geography_fit}
- Investment Thesis: {investor_thesis}

Founder's Focus:
- Sector: {founder_sectors}
- Stage: {founder_stage}
- Location: {founder_location}

Write a professional, formal introduction email with:
1. A compelling subject line (mention the mutual connection)
2. Professional greeting
3. Brief intro mentioning the mutual connection
4. Why this introduction makes sense (use the match reasons)
5. Brief founder background (1-2 sentences, highlight relevant achievements)
6. Why the investor should be interested (sector/stage alignment)
7. Specific call-to-action (suggest a brief call or meeting)
8. Professional closing

Keep the email concise (150-250 words), professional, and focused on value for the investor.
Use proper business email format.

Return ONLY a JSON object with this exact structure:
{{
  "subject": "subject line here",
  "body": "email body here (with proper line breaks using \\n\\n for paragraphs)"
}}
"""

CASUAL_EMAIL_PROMPT = """You are writing a friendly, warm introduction email to connect a founder with an investor.

Context:
- Founder: {founder_name} from {founder_company} ({founder_position})
- Investor: {investor_name} from {investor_company} ({investor_position})
- Mutual Connection: {mutual_connection_name} ({mutual_connection_role})
- Match Score: {match_score}/100

Key Match Reasons:
{match_reasons}

Investment Fit:
- Sector: {sector_fit}
- Stage: {stage_fit}
- Geography: {geography_fit}
- Investment Thesis: {investor_thesis}

Founder's Focus:
- Sector: {founder_sectors}
- Stage: {founder_stage}
- Location: {founder_location}

Write a friendly, casual introduction email with:
1. A warm, approachable subject line
2. Friendly greeting (use first names)
3. Natural mention of mutual connection
4. Why this connection makes sense (conversational tone)
5. Quick founder intro (relatable, not too formal)
6. Why it's a great fit (focus on alignment)
7. Easy call-to-action (coffee chat, quick call)
8. Warm closing

Keep it conversational, warm, and genuine (150-250 words).
Sound like you're talking to a colleague, not writing a formal letter.

Return ONLY a JSON object with this exact structure:
{{
  "subject": "subject line here",
  "body": "email body here (with proper line breaks using \\n\\n for paragraphs)"
}}
"""

ENTHUSIASTIC_EMAIL_PROMPT = """You are writing an excited, enthusiastic introduction email to connect a founder with an investor.

Context:
- Founder: {founder_name} from {founder_company} ({founder_position})
- Investor: {investor_name} from {investor_company} ({investor_position})
- Mutual Connection: {mutual_connection_name} ({mutual_connection_role})
- Match Score: {match_score}/100

Key Match Reasons:
{match_reasons}

Investment Fit:
- Sector: {sector_fit}
- Stage: {stage_fit}
- Geography: {geography_fit}
- Investment Thesis: {investor_thesis}

Founder's Focus:
- Sector: {founder_sectors}
- Stage: {founder_stage}
- Location: {founder_location}

Write an enthusiastic, energetic introduction email with:
1. An exciting subject line that captures the opportunity
2. Warm, enthusiastic greeting
3. Excited mention of mutual connection
4. Why you're thrilled about this match (show genuine excitement)
5. Compelling founder story (highlight what makes them special)
6. Why this is an amazing opportunity for the investor
7. Enthusiastic call-to-action
8. Warm, energetic closing

Be genuine, excited, and compelling (150-250 words).
Show authentic enthusiasm about the match without being over the top.

Return ONLY a JSON object with this exact structure:
{{
  "subject": "subject line here",
  "body": "email body here (with proper line breaks using \\n\\n for paragraphs)"
}}
"""

EMAIL_SYSTEM_PROMPT = "You are an expert at writing warm introduction emails in the venture capital ecosystem. You understand founder-investor dynamics and write compelling, personalized introductions that lead to meetings. Always return valid JSON."
