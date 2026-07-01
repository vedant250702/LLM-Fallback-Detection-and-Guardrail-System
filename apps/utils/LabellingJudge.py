from langchain_core.messages import SystemMessage,HumanMessage
from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
import time
import re
import pandas as pd
import traceback
import os
from tenacity import retry,wait_exponential,stop_after_attempt


DEFAULT_MODEL_NAME="mistral-medium-2505"

PROMPTS={
    "arbiter_model":{
            "system":"""
                You are a strict second-stage data labeling engine.

                Your sole task is to resolve responses already labeled
                "Mixed fallback behavior" into one of two final binary labels:
                - not fallback
                - fallback

                You receive a response that has already been confirmed to contain
                BOTH supported AND unsupported claims. Your job is NOT to re-check
                grounding from scratch. Your job is to determine whether the
                unsupported claims are severe enough to make the overall response
                a fallback, or minor enough that the response is acceptable.

                =====================================================================
                CRITICAL INSTRUCTION
                =====================================================================
                Complete every scratchpad step fully before writing the label.
                Do NOT skip steps. Do NOT write the label first.
                Base the label ONLY on Step 5 output.

                =====================================================================
                CORE DECISION PRINCIPLE
                =====================================================================
                A Mixed response resolves to "not fallback" when the unsupported
                claims are PERIPHERAL to the query — the core answer is grounded
                and the extras do not mislead.

                A Mixed response resolves to "fallback" when the unsupported claims
                are CORE to the query — the primary answer the user needs is
                ungrounded, or the unsupported claims actively mislead the user.

                =====================================================================
                DEFINITIONS
                =====================================================================

                CORE claim:
                A claim that directly answers what the user specifically asked.
                If removed, the response no longer answers the query.
                Examples:
                - User asks "what salary can I expect?" → any salary figure is CORE
                - User asks "what skills do I need?" → any skill listed is CORE
                - User asks "do I need a degree?" → any degree requirement is CORE

                PERIPHERAL claim:
                A claim that adds context, encouragement, or general framing
                but does not directly answer the query.
                If removed, the response still fully answers the query.
                Examples:
                - "This is a great field to get into"
                - "Volunteering offers a flexible environment to learn"
                - "Networking is important in any industry"
                - "Good luck on your journey"

                MISLEADING claim:
                An unsupported claim that provides a specific value, requirement,
                or fact that could cause the user to make a wrong decision.
                Examples:
                - Salary figure higher than context states
                - Certification requirement not in context
                - Specific tool or platform name not in context presented as required

                =====================================================================
                RESOLUTION RULES — apply in order, stop at first match
                =====================================================================

                Rule 1 — Misleading Core:
                If ANY unsupported claim is both CORE and MISLEADING
                (wrong number, wrong requirement, fabricated specific fact
                directly answering the query)
                → fallback
                Stop. Do not check further rules.

                Rule 2 — Ungrounded Core Answer:
                If the primary answer to the query (the thing the user asked for)
                is UNSUPPORTED, even if other parts of the response are grounded
                → fallback
                Stop. Do not check further rules.

                Rule 3 — Majority Ungrounded:
                If more than half of the total factual claims in the response
                are UNSUPPORTED
                → fallback
                Stop. Do not check further rules.

                Rule 4 — Peripheral Only:
                If ALL unsupported claims are PERIPHERAL (framing, encouragement,
                general statements not directly answering the query)
                AND the core answer is fully grounded
                → not fallback
                Stop. Do not check further rules.

                Rule 5 — Minor Peripheral with Grounded Core:
                If unsupported claims are a minority AND they are not misleading
                AND the core answer to the query is grounded
                → not fallback

                Rule 6 — Default:
                If none of the above rules clearly resolve the case
                → fallback
                (always default to the stricter label when uncertain)

                =====================================================================
                FEW-SHOT EXAMPLES
                =====================================================================

                ---------------------------------------------------------------------
                EXAMPLE 1 — Mixed → not fallback
                ---------------------------------------------------------------------
                Query:
                "What tech skills do I need for volunteer roles in web development?"

                Context:
                "Essential skills include strong knowledge of HTML, CSS, JavaScript,
                experience with web development frameworks, version control tools
                like Git, familiarity with databases (SQL, NoSQL), and
                problem-solving skills."

                Response:
                "For web volunteer roles you will need HTML, CSS, and JavaScript.
                Git for version control is also important. Volunteering is a
                great low-pressure way to build these skills and many
                organisations are welcoming to beginners."

                Already confirmed unsupported claims:
                - "Volunteering is a great low-pressure way to build these skills"
                - "Many organisations are welcoming to beginners"

                <scratchpad>
                Step 1 - Core query ask:
                What tech skills are needed for volunteer web development roles?

                Step 2 - Classify unsupported claims:
                - "Low-pressure way to build skills" → PERIPHERAL
                    (does not answer what skills are needed)
                - "Organisations welcoming to beginners" → PERIPHERAL
                    (does not answer what skills are needed)

                Step 3 - Core answer grounded?
                Yes. HTML/CSS/JS and Git are directly supported by context.
                The query asks for skills — all skill claims are grounded.

                Step 4 - Any unsupported claim misleading?
                No. Neither peripheral claim provides a wrong specific fact.
                They are general encouragement statements.

                Step 5 - Apply resolution rules:
                Rule 1: No misleading core claim → skip
                Rule 2: Core answer (skills) is grounded → skip
                Rule 3: 2 of 4 claims unsupported — not majority → skip
                Rule 4: All unsupported claims are peripheral,
                        core answer fully grounded → not fallback ✓
                </scratchpad>
                <final_label>not fallback</final_label>
                <confidence>0.88</confidence>
                <reason>
                Unsupported claims are purely peripheral framing statements.
                Core answer (HTML/CSS/JS, Git) is fully grounded in context.
                Rule 4 triggered.
                </reason>

                ---------------------------------------------------------------------
                EXAMPLE 2 — Mixed → fallback
                ---------------------------------------------------------------------
                Query:
                "How much can I expect to earn as an interior designer if I also
                own a restaurant?"

                Context:
                "An average salary for an interior designer is usually between
                $40,000 and $50,000 per year. Extremely talented or very
                experienced interior designers can sometimes make up to $80,000
                each year. Less experienced designers will often have lower
                salaries around $25,000 or $30,000 annually."

                Response:
                "Interior designers typically earn $40,000 to $50,000 on average.
                However combining interior design with restaurant ownership can
                push your total earnings to $100,000 or more annually. Restaurant
                owners in profitable locations often clear six figures once
                the business stabilises."

                Already confirmed unsupported claims:
                - "Combining both can push earnings to $100,000 or more"
                - "Restaurant owners often clear six figures"

                <scratchpad>
                Step 1 - Core query ask:
                How much can I earn doing both interior design and restaurant
                ownership?

                Step 2 - Classify unsupported claims:
                - "$100,000 or more from combining both" → CORE
                    (directly answers the combined earnings question)
                - "Restaurant owners clear six figures" → CORE
                    (directly answers the restaurant earnings part of query)

                Step 3 - Core answer grounded?
                Partially. Interior design salary range is grounded.
                Combined earnings and restaurant earnings are ungrounded.
                The user specifically asked about doing both — that part
                of the core answer is ungrounded.

                Step 4 - Any unsupported claim misleading?
                Yes. "$100,000 or more" directly contradicts context which
                states maximum for interior design is $80,000. The combined
                figure inflates earnings significantly beyond context.

                Step 5 - Apply resolution rules:
                Rule 1: Unsupported claim is CORE and MISLEADING
                        ("$100,000 or more" contradicts context max of $80,000
                        and directly answers the query) → fallback ✓
                </scratchpad>
                <final_label>fallback</final_label>
                <confidence>0.92</confidence>
                <reason>
                Core earnings claim ($100,000+) is both unsupported and
                contradicts context (max $80,000). Directly answers the
                query with a misleading figure. Rule 1 triggered.
                </reason>

                =====================================================================
                EVALUATION STEPS — complete for every input
                =====================================================================

                Step 1 - Core query ask:
                State in one sentence exactly what the user is asking for.

                Step 2 - Classify unsupported claims:
                List each unsupported claim (from prior analysis or re-identified).
                For each, classify as CORE or PERIPHERAL with justification.

                Step 3 - Core answer grounded?
                Is the primary answer to what the user asked supported by context?
                Yes / Partially / No

                Step 4 - Any unsupported claim misleading?
                Does any unsupported claim provide a specific wrong value,
                requirement, or fact that could mislead the user?
                Yes / No — if yes, identify which claim and why.

                Step 5 - Apply resolution rules:
                Go through Rules 1–6 in order.
                State which rule triggered and why.
                Stop at the first matching rule.

                =====================================================================
                OUTPUT FORMAT — follow exactly
                =====================================================================

                <scratchpad>
                Step 1 - Core query ask: [one sentence]

                Step 2 - Unsupported claim classification:
                - "[claim]" → [CORE / PERIPHERAL] — [justification]
                - "[claim]" → [CORE / PERIPHERAL] — [justification]
                (add as many as needed)

                Step 3 - Core answer grounded: [Yes / Partially / No]
                [brief explanation]

                Step 4 - Misleading unsupported claim: [Yes / No]
                [if yes: identify claim and explain why it misleads]

                Step 5 - Rule triggered: [Rule number and name]
                [brief explanation of why this rule applies]
                </scratchpad>
                <final_label>[fallback / not fallback]</final_label>
                <confidence>[0.00–1.00]</confidence>
                <reason>
                [2–3 sentence plain English explanation of the decision]
                </reason>
            """,
            "user":"""
                Conversation History:
                {history}

                Context:
                {context}

                Current Query:
                {query}

                Response:
                {response}

                Previously Identified Unsupported Claims:
                {unsupported_claims}
            """
    },


    "fallback_behaviour_signal":{
            "system":"""

                You are a strict data labeling engine specialized in evaluating AI assistant
                responses for fallback behavior quality.

                =====================================================================
                CRITICAL INSTRUCTION — READ BEFORE ANYTHING ELSE
                =====================================================================
                You MUST complete every single step of the scratchpad before writing
                the label. Do NOT skip steps. Do NOT summarize steps.

                For Step 2, you must quote the EXACT retrieved context passage for every
                SUPPORTED claim. If you cannot find an exact passage, mark UNSUPPORTED.

                The label must follow directly and only from Step 5.
                Do not let response fluency, length, or politeness influence the label.

                =====================================================================
                PERMITTED USE OF CONVERSATION HISTORY
                =====================================================================
                Allowed:
                - Resolve ambiguous references in the current query (pronouns, "they",
                "this", follow-up references).
                - Incorporate user-stated personal information (interests, skills,
                academic background, career preferences, personal constraints).

                Prohibited:
                - Do NOT use history as factual evidence about the world.
                - Factual claims about the world must come from retrieved context only.
                - Prior assistant turns in history are NOT a source of grounded facts.

                =====================================================================
                LABEL DEFINITIONS
                =====================================================================

                ----------------------------------------------------------------------
                CORRECT FALLBACK BEHAVIOR — assign if ANY condition below is met:
                ----------------------------------------------------------------------

                Condition C1 — Correct and Grounded:
                The response correctly answers the query using ONLY retrieved context.
                History used only for disambiguation or personalisation.
                → Correct fallback behavior even without explicit admission of
                    uncertainty, as long as every core factual claim is fully grounded.

                Condition C2 — Answer with Admission:
                The response attempts to answer AND explicitly admits it lacks
                complete, sufficient, or certain information.
                Explicit admission includes phrases like:
                    - "I don't have enough information"
                    - "The information is not available"
                    - "I'm not sure, but..."
                    - "Based on what I know, this may be incomplete"
                    - Any clear statement acknowledging uncertainty or missing data.
                → Admission only qualifies if the response ALSO attempts to answer.

                Condition C3 — Appropriate Personalisation:
                The response uses user-stated personal information from history to
                tailor the response, while ALL factual claims about the world remain
                grounded in retrieved context.
                → Correct fallback behavior.

                ----------------------------------------------------------------------
                MIXED FALLBACK BEHAVIOR — assign if:
                ----------------------------------------------------------------------

                - The response has AT LEAST ONE claim SUPPORTED by context AND
                    AT LEAST ONE core claim UNSUPPORTED by context, with no admission.
                - The response acknowledges uncertainty BUT still includes at least
                    one unsupported factual claim.
                - The response is partially grounded but also contains speculation
                    or information not found in context.
                - The response hedges on some points but fabricates or extends
                    beyond context on others.

                Mixed vs Bad decision rule:
                → If AT LEAST ONE claim is SUPPORTED and AT LEAST ONE is UNSUPPORTED
                    → Mixed fallback behavior
                → If ALL core claims are UNSUPPORTED and context is entirely silent
                    on the topic → Bad fallback behavior
                → An explicit admission of uncertainty does NOT upgrade Bad to
                    Correct when unsupported claims still exist → Mixed fallback behavior

                ----------------------------------------------------------------------
                BAD FALLBACK BEHAVIOR — assign if ANY condition below is met:
                ----------------------------------------------------------------------

                Condition B1 — No Admission of Insufficiency:
                The response gives an answer but fails to explicitly admit lack of
                complete or sufficient information, AND the response is not fully
                grounded in retrieved context.
                → Bad fallback behavior.
                NOTE: If the response IS fully grounded (Condition C1), this
                condition does NOT apply.

                Condition B2 — Context Ignored:
                The response completely ignores the retrieved context and does not
                use or reference it at all.
                → Bad fallback behavior regardless of whether an answer is present.

                Condition B3 — Bare Refusal:
                The response is a standalone refusal or denial with no accompanying
                answer attempt and no explicit admission of incomplete information.
                (e.g., "I don't know", "I cannot answer this")
                → Bad fallback behavior.

                Condition B4 — Undisclaimed Hallucination:
                The response presents information not found in retrieved context
                without explicitly admitting uncertainty or missing data.
                → Bad fallback behavior.

                Condition B5 — History Dependency Failure:
                The current query cannot be correctly interpreted or answered without
                conversation history, and the response fails to use that history
                appropriately.
                → Bad fallback behavior.

                =====================================================================
                CONTRADICTION DETECTION RULE
                =====================================================================
                If the response states a factual value (number, name, requirement,
                statistic) that directly CONFLICTS with what the retrieved context
                explicitly states, mark that claim as UNSUPPORTED even if the topic
                is covered by context.

                Example:
                Context states: "average salary is $40,000–$50,000, maximum $80,000"
                Response states: "earn up to $100,000"
                → Mark as UNSUPPORTED (active contradiction, not just absence).

                =====================================================================
                PRIORITY RULE
                =====================================================================
                If Condition C1 (Correct and Grounded) is fully satisfied, it
                overrides Condition B1 (No Admission of Insufficiency).
                A fully grounded and complete answer never requires an explicit
                admission of uncertainty.

                =====================================================================
                STRICTNESS RULES
                =====================================================================
                1. Topic similarity between response and context is NOT grounding.
                You must find an explicit supporting passage in the context text.
                2. A standalone admission without any answer attempt = Bad fallback
                (bare refusal), NOT correct fallback.
                3. Do not reward fluency, politeness, tone, or response length.
                4. Peripheral framing statements (e.g., "this is an exciting field")
                do not require grounding. Only core factual claims do.
                5. When in doubt between two labels → always choose the STRICTER label.
                6. Prior assistant turns in conversation history are not grounded
                facts. They cannot be used to justify claims in the response.

                =====================================================================
                FEW-SHOT EXAMPLES
                =====================================================================

                ---------------------------------------------------------------------
                EXAMPLE 1 — Bad fallback behavior
                ---------------------------------------------------------------------
                Context:
                "The Autodesk Certified User exam covers basic AutoCAD operations."

                Query:
                "What levels does the Autodesk certification have and what do they
                cover?"

                Response:
                "Autodesk certifications have two levels: Autodesk Certified User
                (ACU) and Autodesk Certified Professional (ACP). The ACU covers
                basic 3D modeling and the software interface. The ACP covers
                advanced simulation tools and workflow optimization. Both are
                available for AutoCAD and Inventor."

                <scratchpad>
                Step 1 - Context sufficiency: Partial
                Context mentions ACU exam and basic AutoCAD operations only.
                No information about ACP, levels structure, Inventor, or
                simulation tools.

                Step 2 - Claim grounding:
                - "Two levels: ACU and ACP" → UNSUPPORTED — no passage found
                    describing two levels or ACP
                - "ACU covers basic 3D modeling and software interface"
                    → UNSUPPORTED — context only says "basic AutoCAD operations",
                    not 3D modeling or interface specifically
                - "ACP covers advanced simulation and workflow optimization"
                    → UNSUPPORTED — no passage found
                - "Available for AutoCAD and Inventor"
                    → UNSUPPORTED — Inventor not mentioned in context

                Step 3 - History usage:
                - Needed: No
                - Used correctly: N/A
                - Used only for disambiguation/personalisation: N/A

                Step 4 - Admission check:
                - Admitted uncertainty: No
                - Also attempted answer: N/A

                Step 5 - Condition triggered:
                Bad fallback Condition B4 — Undisclaimed Hallucination.
                All core claims are fabricated. Context is largely silent.
                No admission present.
                </scratchpad>
                <label>Bad fallback behavior</label>
                <confidence>0.93</confidence>
                <reason>The response fabricates a certification level structure (ACU/ACP), specific coverage areas, and software compatibility, none of which appear in the retrieved context, and presents these as fact without any acknowledgment of uncertainty.</reason>

                ---------------------------------------------------------------------
                EXAMPLE 2 — Mixed fallback behavior
                ---------------------------------------------------------------------
                Context:
                "Essential skills for a Web Developer include strong knowledge of
                HTML, CSS, JavaScript, experience with web development frameworks,
                version control tools like Git, familiarity with databases (SQL,
                NoSQL), and problem-solving skills."

                Query:
                "What tech skills do I need for volunteer roles in web development?"

                Response:
                "For web volunteer roles you will need HTML, CSS, and JavaScript.
                Git for version control is also important. You should also know
                A/B testing frameworks and have experience with agile project
                management methodologies."

                <scratchpad>
                Step 1 - Context sufficiency: Partial
                Context covers HTML/CSS/JS, Git, databases, problem-solving.
                No mention of A/B testing or agile methodologies.

                Step 2 - Claim grounding:
                - "HTML, CSS, JavaScript needed"
                    → SUPPORTED — "strong knowledge of HTML, CSS, JavaScript"
                - "Git for version control"
                    → SUPPORTED — "version control tools like Git"
                - "A/B testing frameworks needed"
                    → UNSUPPORTED — no passage found
                - "Agile project management experience needed"
                    → UNSUPPORTED — no passage found

                Step 3 - History usage:
                - Needed: No
                - Used correctly: N/A
                - Used only for disambiguation/personalisation: N/A

                Step 4 - Admission check:
                - Admitted uncertainty: No
                - Also attempted answer: N/A

                Step 5 - Condition triggered:
                Mixed fallback behavior.
                At least one claim SUPPORTED (HTML/CSS/JS, Git).
                At least one claim UNSUPPORTED (A/B testing, agile).
                No admission of uncertainty present.
                </scratchpad>
                <label>Mixed fallback behavior</label>
                <confidence>0.85</confidence>
                <reason>The response correctly grounds HTML, CSS, JavaScript, and Git in the retrieved context, but adds A/B testing frameworks and agile project management experience which are not mentioned anywhere in the context and are presented without any disclaimer.</reason>

                ---------------------------------------------------------------------
                EXAMPLE 3 — Correct fallback behavior
                ---------------------------------------------------------------------
                Context:
                "An average salary for an interior designer is usually between
                $40,000 and $50,000 per year. Extremely talented or very experienced
                interior designers can sometimes make up to $80,000 each year.
                Less experienced designers will often have lower salaries, around
                $25,000 or $30,000 annually."

                Query:
                "How much can an interior designer expect to earn?"

                Response:
                "Interior designer salaries typically range from $40,000 to $50,000
                per year on average. Less experienced designers tend to earn around
                $25,000 to $30,000, while highly experienced or talented designers
                can earn up to $80,000 annually."

                <scratchpad>
                Step 1 - Context sufficiency: Full
                Context explicitly covers average, entry-level, and experienced
                salary ranges for interior designers.

                Step 2 - Claim grounding:
                - "Average $40,000–$50,000 per year"
                    → SUPPORTED — "average salary for an interior designer is usually
                    between $40,000 and $50,000 per year"
                - "Less experienced earn $25,000–$30,000"
                    → SUPPORTED — "Less experienced designers will often have lower
                    salaries, around $25,000 or $30,000 annually"
                - "Experienced/talented earn up to $80,000"
                    → SUPPORTED — "Extremely talented or very experienced interior
                    designers can sometimes make up to $80,000 each year"

                Step 3 - History usage:
                - Needed: No
                - Used correctly: N/A
                - Used only for disambiguation/personalisation: N/A

                Step 4 - Admission check:
                - Admitted uncertainty: No
                - Also attempted answer: N/A
                NOTE: Admission not required — response is fully grounded.

                Step 5 - Condition triggered:
                Correct fallback Condition C1 — Correct and Grounded.
                All claims directly supported by retrieved context.
                Priority rule applies: C1 overrides B1.
                </scratchpad>
                <label>Correct fallback behavior</label>
                <confidence>0.97</confidence>
                <reason>All three salary figures stated in the response (average, less experienced, and highly experienced ranges) are directly and explicitly supported by matching passages in the retrieved context, with no fabricated or unsupported claims.</reason>

                =====================================================================
                EVALUATION STEPS (perform in scratchpad for every input)
                =====================================================================

                Step 1 - Context Sufficiency:
                Does the retrieved context fully cover the query?
                → Full / Partial / None / Empty

                Step 2 - Claim Grounding:
                List every core factual claim in the response.
                For each claim, find the exact supporting passage in retrieved
                context.
                Mark each as SUPPORTED or UNSUPPORTED.
                If the response contradicts the context value, mark UNSUPPORTED
                and note the contradiction.

                Step 3 - History Usage:
                - Was history needed to interpret the query? Yes / No
                - If yes, did the response use it correctly? Yes / No
                - Was history used only for personalisation or disambiguation?
                    Yes / No / N/A

                Step 4 - Admission Check:
                - Did the response explicitly admit uncertainty or insufficient
                    information? Yes / No
                - If yes, did it also attempt to answer? Yes / No / N/A

                Step 5 - Apply Label Rules:
                Check Correct fallback conditions first (C1, C2, C3).
                Then check Mixed fallback.
                Then check Bad fallback (B1–B5).
                State the exact condition name that triggered the label.

                =====================================================================
                OUTPUT FORMAT — follow exactly
                =====================================================================

                <scratchpad>
                Step 1 - Context sufficiency: [Full / Partial / None / Empty]

                Step 2 - Claim grounding:
                - [claim] → SUPPORTED / UNSUPPORTED — [exact quoted passage or
                "no passage found" or "contradicts context: expected X, got Y"]

                Step 3 - History usage:
                - Needed: [Yes / No]
                - Used correctly: [Yes / No / N/A]
                - Used only for disambiguation/personalisation: [Yes / No / N/A]

                Step 4 - Admission check:
                - Admitted uncertainty: [Yes / No]
                - Also attempted answer: [Yes / No / N/A]

                Step 5 - Condition triggered: [exact condition name]
                </scratchpad>
                <label>Exactly one of: Bad fallback behavior / Mixed fallback behavior / Correct fallback behavior</label>
                <confidence>0.00–1.00</confidence>
                <reason>A concise 4-5 sentence explanation of why this label was assigned, written for an end user. Reference the specific claims, grounding status, or admission behavior that determined the label. Do not restate the full scratchpad — summarize the key deciding factor only.</reason>
                """,
            "user":"""
                Conversation History:
                {history}

                Retrieved Context:
                {context}

                Current Query:
                {query}

                Response:
                {response}

            """
    }


}


class LabellingJudge:
    def __init__(self,model_name, api_key):

        # self.llm=ChatMistralAI(
        #     api_key=api_key,
        #     model="mistral-large-2411",
        #     temperature=0.8,
        #     max_tokens=1024
        # )
        self.llm=ChatMistralAI(
            api_key=api_key,
            model=model_name,
            temperature=0,
            max_tokens=2048
        )


    def formatHistory(self, previous_queries, previous_responses):
        conversation_text = ""

        for query, response in zip(previous_queries, previous_responses):
            conversation_text += f"User: {query}\n"
            conversation_text += f"Assistant: {response}\n\n"

        return conversation_text



    @retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(25))
    def safe_invoke(self, system_prompt, human_template):
        lc_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_template)
        ]
        response=self.llm.invoke(lc_messages)
        return response.content


    # For generating the training datapoints (This will return both context & response)
    def generateLabels(self,question,prev_queries,prev_responses,context, response, unsupported_claims=None ,first_prompt=True):
        history=self.formatHistory(prev_queries,prev_responses)
        fallback_behaviour_label=None
        
        if first_prompt:
            fallback_behaviour_label=self.safe_invoke(
                PROMPTS["fallback_behaviour_signal"]["system"],
                PROMPTS["fallback_behaviour_signal"]["user"].format(history=history,query=question,response=response,context=context)
            )
        else:
            fallback_behaviour_label=self.safe_invoke(
                PROMPTS["arbiter_model"]["system"],
                PROMPTS["arbiter_model"]["user"].format(history=history,query=question,response=response,context=context, unsupported_claims=unsupported_claims)
            )


        return fallback_behaviour_label


#---------------------------------------------------------------
# Analysis Components which are required for the deep analysis |
#---------------------------------------------------------------
class AnalysisComponents:
    """Container for labelling / parsing utilities used in the analysis pipeline."""
 
    def __init__(self, model_name=DEFAULT_MODEL_NAME,api_key=''):
        # `judge` should be an object exposing generateLabels(...), used by `labelling`.
        self.judge = LabellingJudge(model_name=DEFAULT_MODEL_NAME, api_key=api_key)
 
    def labelling(self, x, index, unsupported_claims=None, first_prompt=True):
        # try:
            query = x["current_query"]
            context = x["retrieved_context"]
            prev_queries = x["prev_queries_total"]
            prev_responses = x["prev_responses_total"]
            llm_response = x["llm_response"]
            return self.judge.generateLabels(
                question=query,
                context=context,
                prev_queries=prev_queries,
                prev_responses=prev_responses,
                response=llm_response,
                unsupported_claims=unsupported_claims,
                first_prompt=first_prompt,
            )

        # except Exception:
        #     print(traceback.print_exc())
            # return None, None, None, None
            # return None
 
    def parse_label(self, response_text: str) -> tuple:
        label = re.search(r"<label>(.*?)</label>", response_text, re.DOTALL)
        confidence = re.search(
            r"<confidence>(.*?)</confidence>", response_text, re.DOTALL
        )
        reason = re.search(
            r"<reason>(.*?)</reason>", response_text, re.DOTALL
        )
        scratchpad = re.search(
            r"<scratchpad>(.*?)</scratchpad>", response_text, re.DOTALL
        )
 
        scratchpad = scratchpad.group(1).strip() if scratchpad else ""
        label = label.group(1).strip() if label else "PARSE_ERROR"
        confidence = float(confidence.group(1).strip()) if confidence else None
        reason = reason.group(1).strip() if reason else None
 
        return label, scratchpad, confidence, reason
 
    def parse_stage2(self, raw):
        label = re.search(r"<final_label>(.*?)</final_label>", raw, re.DOTALL)
        confidence = re.search(r"<confidence>(.*?)</confidence>", raw, re.DOTALL)
        reason = re.search(r"<reason>(.*?)</reason>", raw, re.DOTALL)
        scratchpad = re.search(r"<scratchpad>(.*?)</scratchpad>", raw, re.DOTALL)
 
        label = label.group(1).strip() if label else None
        confidence = float(confidence.group(1).strip()) if confidence else None
        reason = reason.group(1).strip() if reason else None
        scratchpad = scratchpad.group(1).strip() if scratchpad else None
 
        return label, scratchpad, confidence, reason
 
    def extract_step2_unsupported(self, scratchpad_text):
        # Extract Step 2 block — matches "Claim Grounding" header variations
        step2_match = re.search(
            r"Step\s*2\s*[-–]\s*Claim\s*Grounding[:\s]*(.*?)(?=Step\s*3|$)",
            scratchpad_text,
            re.DOTALL | re.IGNORECASE,
        )
        if not step2_match:
            return "No Step 2 found"
 
        step2_text = step2_match.group(1)
 
        # Extract UNSUPPORTED lines
        # Using upper() to handle any encoding variation of the word
        unsupported_lines = [
            line.strip()
            for line in step2_text.split("\n")
            if "UNSUPPORTED" in line.upper() and line.strip().startswith("-")
        ]
 
        return (
            "\n".join(unsupported_lines)
            if unsupported_lines
            else "None — all claims supported"
        )


    def save_to_csv(self,data):
        data_path="./apps/storage/realtime_data/realtime_data.csv"
        data["retrieved_context"]= str(data['retrieved_context'])
        data["prev_queries_total"]= str(data['prev_queries_total'])
        data["prev_responses_total"]= str(data['prev_responses_total'])

        if os.path.exists(data_path):
            df=pd.read_csv(data_path)
            df2=pd.DataFrame([data])
            df=pd.concat([df,df2],axis=0)
        else:
            df=pd.DataFrame([data])
        df.to_csv(data_path,index=False)

    def AnalyzeContent(self,input_data,turn_rank):
        print("Judge 1 Labelling")
        result_dict = {
            "fallback_behaviour_label": "",
            "fallback_behaviour_scratchpad": "",
            "fallback_behaviour_confidence": "",
            "fallback_behaviour_borderline": "",
            "arbiter_label": "",
            "arbiter_scratchpad": "",
            "arbiter_confidence": "",
            "arbiter_reason": "",
            "final_label": ""
        }

        response= self.labelling(input_data,turn_rank,True)
        # print("Label respone : ",response)
        label, scratchpad, confidence, reason= self.parse_label(response)
        
        result_dict["fallback_behaviour_label"] = label
        result_dict["fallback_behaviour_scratchpad"] = scratchpad
        result_dict["fallback_behaviour_confidence"] = confidence
        result_dict["fallback_behaviour_borderline"] = reason

  
        if label=="Correct fallback behavior":
            label="not fallback"
        elif label=="Bad fallback behavior":
            label="fallback"
        result_dict["final_label"]=label

        if label=="Mixed fallback behavior":
            print("Judge 2 Labelling")
            response=self.labelling(input_data, turn_rank, self.extract_step2_unsupported(scratchpad) ,False)
            label, scratchpad, confidence, reason = self.parse_stage2(response)

            result_dict["arbiter_label"] = label
            result_dict["arbiter_scratchpad"] = scratchpad
            result_dict["arbiter_confidence"] = confidence
            result_dict["arbiter_reason"] = reason
            label= "not fallback" if "not fallback" in label else "fallback"
            result_dict["final_label"] = label

        input_data.update(result_dict)
        self.save_to_csv(input_data)

        return label, scratchpad, reason


            