from typing import List, Dict, Optional
from src.config import GEMINI_API_KEY, DEFAULT_MODEL
from src.schemas import Question, SocraticHint

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


class SocraticTutorAgent:
    """
    Socratic AI Tutor Agent:
    Strictly guides students through inquiry rather than giving away direct answers.
    Uses a 3-tier scaffolding ladder:
      - Level 1 (Nudge): Draws attention to the core question or a critical clue.
      - Level 2 (Scaffold): Prompts for the underlying mathematical or logical principle.
      - Level 3 (Step-Through): Models the first milestone step and asks the student to finish.
    """

    def __init__(self):
        self.client = None
        if GEMINI_API_KEY and genai:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[SocraticTutorAgent] Client error: {e}")

    def generate_hint(
        self,
        question: Question,
        student_mistake: Optional[str] = None,
        hint_level: int = 1,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> SocraticHint:
        """Generates a pedagogical hint strictly avoiding raw answers."""
        # Question-specific simple clues for maximum clarity
        specific_hints = {
            "sat_linear_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Start by finding the slope of the given line 3x - 6y = 12. Rearrange it into y = mx + b.",
                    guiding_question="When you divide 3x by 6, what number is in front of x?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Perpendicular lines have negative reciprocal slopes: flip the fraction upside down and change the plus/minus sign!",
                    guiding_question="If the first slope is 1/2, what is the negative reciprocal slope?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do Step 1 together: Your new slope is m = -2, and it passes through (2, -1). Use the formula y - y₁ = m(x - x₁).",
                    guiding_question="What equation do you get after simplifying y - (-1) = -2(x - 2)?"
                )
            },
            "sat_systems_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Look at the condition for NO solution: Two lines have no solution when they are parallel (equal slopes) but have different y-intercepts.",
                    guiding_question="What must be true about the ratio of the x-coefficients compared to the y-coefficients?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Set up the ratio: 2 / k must equal -3 / -6. Simplify the fraction -3 / -6 first.",
                    guiding_question="What fraction do you get when you simplify -3 / -6?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do Step 1 together: -3 / -6 simplifies to 1/2. So 2 / k = 1/2. Cross multiply to find k.",
                    guiding_question="If 2 / k = 1 / 2, what does k equal?"
                )
            },
            "sat_quad_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="The equation f(x) = 2(x - 3)² - 8 is in vertex form: f(x) = a(x - h)² + k. Notice where the vertex is located!",
                    guiding_question="Does the question ask for the x-coordinate (where it occurs) or the minimum value of the function itself (the y-value)?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Because (x - 3)² is squared, its smallest possible value is 0 (which happens when x = 3).",
                    guiding_question="When the squared part equals 0, what number is left over?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do Step 1 together: Plug in (x - 3)² = 0: f(x) = 2(0) - 8 = -8. This is the lowest point on the curve.",
                    guiding_question="What is the final minimum value?"
                )
            },
            "sat_circle_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Look carefully at what the question asks for: It wants the actual radius 'r', NOT radius squared (r²).",
                    guiding_question="Do you need to find the center of the circle, or just the radius?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Remember the circle formula: (x - h)² + (y - k)² = r². Notice the number on the right side is r² (radius squared)!",
                    guiding_question="If completing the square gives 36 on the right side, what does r² equal?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do the first step together: We know r² = 36. To find the radius r, just take the square root of 36.",
                    guiding_question="What number multiplied by itself equals 36?"
                )
            },
            "sat_rw_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Read the passage carefully: What is the main idea connecting Arizona dock roots, local plants, and nearby soil?",
                    guiding_question="Where does Lillie Taylor get the materials she uses to create her wool dyes?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Notice the author's emphasis: dock roots from Arizona, plants from where she lives, and clay from nearby soil. They are all local resources.",
                    guiding_question="Which choice directly mentions her use of local resources without adding outside claims?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's test the choices: Choice B says the opposite of the text, Choice C talks about acclaim not mentioned, and Choice D invents a problem. Look at Choice A.",
                    guiding_question="Does Choice A directly match the central idea of the passage?"
                )
            },
            "sat_official_math_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Remember the slope formula: Slope m = (Change in y) divided by (Change in x).",
                    guiding_question="Which values go on top: the y-values or the x-values?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="For the two points (0, 4) and (5, 14), the change in y is (14 - 4), and the change in x is (5 - 0).",
                    guiding_question="What numbers do you get on the top and bottom of the fraction?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do Step 1 together: 14 - 4 = 10 on top, and 5 - 0 = 5 on the bottom. Now divide 10 by 5.",
                    guiding_question="What is 10 divided by 5?"
                )
            },
            "gat_seq_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="We are given: Farooq lectures on Monday (Day 1) and Imran on Wednesday (Day 3). Hamid and Khalid must lecture back-to-back: [Hamid, Khalid].",
                    guiding_question="Can [Hamid, Khalid] fit on Thursday and Friday?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Remember the rule: Khalid cannot lecture on Saturday. So [Hamid, Khalid] cannot be on Friday and Saturday.",
                    guiding_question="Since [Hamid, Khalid] must be placed on Thursday and Friday, which day does Khalid lecture?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Hamid lectures on Thursday (Day 4), and Khalid lectures immediately after him.",
                    guiding_question="What day comes immediately after Thursday?"
                )
            },
            "gat_group_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Look closely at Rule 1: 'If Ali is selected, Bilal must also be selected.' The problem states Ali IS selected!",
                    guiding_question="Based directly on Rule 1, who must immediately join Ali on the committee?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Because Ali is selected, Bilal is definitely selected. Now check Rule 3: 'Bilal and Fahad cannot both be selected.'",
                    guiding_question="Can Fahad be on the committee if Bilal is already there?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's review: Ali is picked, so Rule 1 directly guarantees that Bilal must also be on the committee.",
                    guiding_question="Which option has Bilal?"
                )
            },
            "gat_scenario_01": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="List the 6 days: Mon, Tue, Wed, Thu, Fri, Sat. Imran is on Wednesday (Day 3), and Hamid and Khalid take Thursday (Day 4) and Friday (Day 5).",
                    guiding_question="Which three days are left open for the remaining professors?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Days left: Monday, Tuesday, Saturday. The professors left are Farooq, Ghazala, and Junaid. Remember: Farooq CANNOT be on Saturday, and Farooq must lecture before Ghazala (F < G).",
                    guiding_question="If Farooq must lecture before Ghazala and cannot take Saturday, which days must Farooq and Ghazala take?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Farooq must take Monday, and Ghazala must take Tuesday. That leaves only Saturday open.",
                    guiding_question="Which professor is left to take Saturday?"
                )
            },
            "sat_linear_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Write down the relationship: Total Cost = Flat Visit Fee + (Hourly Rate × Hours).",
                    guiding_question="What is the total cost, and what is the flat fee you must subtract first?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Subtract the $50 flat fee from the $190 total cost: 190 - 50 = 140. That leaves $140 for the hourly work.",
                    guiding_question="If the technician charges $35 per hour, how do you find the hours from 140?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do Step 1 together: Divide 140 by 35 to get the number of hours.",
                    guiding_question="What is 140 divided by 35?"
                )
            },
            "sat_systems_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Notice the y-terms in the two equations: you have +2y in the first equation and -2y in the second equation.",
                    guiding_question="What happens to the y-terms if you add the two equations together?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Add the equations straight down: (3x + x) + (2y - 2y) = 16 + 8.",
                    guiding_question="What does 3x + x equal, and what does 16 + 8 equal?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do Step 1 together: 4x = 24. Now divide 24 by 4 to solve for x.",
                    guiding_question="What is 24 divided by 4?"
                )
            },
            "sat_quad_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="To solve x² - 7x + 10 = 0 by factoring, look for two numbers that multiply to 10 and add to -7.",
                    guiding_question="What two negative numbers multiply to +10 and add to -7?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="The numbers are -2 and -5, so the equation factors into (x - 2)(x - 5) = 0.",
                    guiding_question="When you set (x - 2) = 0 and (x - 5) = 0, what values do you get for x?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do Step 1 together: x - 2 = 0 gives x = 2, and x - 5 = 0 gives x = 5.",
                    guiding_question="Which choice has x = 2 and x = 5?"
                )
            },
            "sat_circle_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Remember the circle center formula: (x - h)² + (y - k)² = r², where the center is (h, k).",
                    guiding_question="Remember to flip the sign inside the parentheses: what is the sign of h and k?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="For (x + 5), think of it as (x - (-5)), so h = -5. For (y - 2), k = 2.",
                    guiding_question="Putting h and k together as (h, k), what point do you get?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="The center is (-5, 2). Notice how the x-value is negative and the y-value is positive.",
                    guiding_question="Which choice matches (-5, 2)?"
                )
            },
            "sat_rw_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Read both sentences: The first sentence says bamboo grows rapidly. The second sentence explains that this makes it one of the most sustainable materials.",
                    guiding_question="Is the second sentence an opposite contrast, or is it a result/consequence of the first sentence?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Because it is a direct cause and effect, you need a transition word that means 'as a result'.",
                    guiding_question="Which transition word means 'as a result' or 'therefore'?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="'Consequently' means 'as a result'. Words like 'However' and 'In contrast' are wrong because there is no disagreement.",
                    guiding_question="Which option says 'Consequently,'?"
                )
            },
            "sat_official_math_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="First, solve for 3x from the equation: 3x + 7 = 22.",
                    guiding_question="When you subtract 7 from 22, what does 3x equal?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="3x = 15. Notice that the question asks for 6x + 5, and 6x is simply twice 3x!",
                    guiding_question="If 3x = 15, what is 6x?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Let's do Step 1 together: 6x = 30. Now add 5 to complete the expression 6x + 5.",
                    guiding_question="What is 30 + 5?"
                )
            },
            "gat_seq_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="We are given: D is 1st (Position 1) and E is 5th (Position 5). Positions 2, 3, and 4 are open for A, B, and C.",
                    guiding_question="Which three positions are left for A, B, and C?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="Remember: B and C must finish consecutively as [B][C], and A must finish before B (A < B).",
                    guiding_question="If A is before [B][C] in positions 2, 3, 4, who must be in position 2, 3, and 4?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="A takes 2nd, B takes 3rd, and C takes 4th. That satisfies both rules.",
                    guiding_question="Which position does B finish in?"
                )
            },
            "gat_group_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="We are told X is selected. Rule 1 says: If X is selected, Y CANNOT be selected. Rule 3 says: V is ALWAYS selected.",
                    guiding_question="Who is excluded, and who is definitely on the panel alongside X?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="So far we have X and V. We need 1 more judge to make a panel of 3. Look at Rule 2: 'Either Z or W must be selected, but not both.'",
                    guiding_question="Where must the third judge come from?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="The panel must be X, V, and either Z or W.",
                    guiding_question="Which option lists V and either Z or W?"
                )
            },
            "gat_scenario_02": {
                1: SocraticHint(
                    hint_level=1,
                    hint_text="Read the rules carefully: Imran is fixed on Wednesday (Day 3).",
                    guiding_question="Does placing other professors on Monday or Tuesday change the professor fixed on Wednesday?"
                ),
                2: SocraticHint(
                    hint_level=2,
                    hint_text="No matter where [Hamid, Khalid] are placed, Imran is permanently scheduled for Wednesday.",
                    guiding_question="Which professor is scheduled for Wednesday?"
                ),
                3: SocraticHint(
                    hint_level=3,
                    hint_text="Imran is explicitly set on Wednesday by Rule 1.",
                    guiding_question="Which option says Imran?"
                )
            }
        }

        if question.id in specific_hints and hint_level in specific_hints[question.id]:
            return specific_hints[question.id][hint_level]

        # General friendly fallback hints
        default_hints = {
            1: SocraticHint(
                hint_level=1,
                hint_text="Let's look at the question together: What are the given values, and what exact number or letter are you asked to find?",
                guiding_question="What is the final answer you are trying to calculate?"
            ),
            2: SocraticHint(
                hint_level=2,
                hint_text=f"Think about the main rule or formula for '{question.topic}'. Write down the formula on paper.",
                guiding_question="Which formula or rule applies directly here?"
            ),
            3: SocraticHint(
                hint_level=3,
                hint_text="Let's do the first step together: Plug the first number you know into the formula and solve that part first.",
                guiding_question="Once you do that first calculation, what do you get?"
            )
        }

        if not self.client:
            return default_hints.get(hint_level, default_hints[1])

        level_descriptions = {
            1: "LEVEL 1 (NUDGE): Do NOT reveal any math formulas or answers. Ask an orienting question to make the student re-read a key phrase or recognize the primary objective.",
            2: "LEVEL 2 (SCAFFOLD): Remind them of the conceptual framework or ask them to identify the relevant theorem/rule without doing the math for them.",
            3: "LEVEL 3 (STEP-THROUGH): Walk through Step 1 explicitly, but STOP and prompt the student to complete Step 2 and find the final result."
        }

        system_instruction = f"""
You are a master Socratic tutor for standardized tests ({question.exam_type}).
CRITICAL PEDAGOGICAL RULE:
You are STRICTLY FORBIDDEN from giving the direct final answer (e.g. 'The answer is A' or 'x = 3').
Your mission is to help the student reach the 'Aha!' moment themselves.

CURRENT HINT LEVEL: {level_descriptions[hint_level]}

QUESTION:
{question.question}

OPTIONS:
{chr(10).join([f"{opt.key}: {opt.text}" for opt in question.options])}

STUDENT'S MISTAKE / ERROR:
{student_mistake or 'Student requested a hint'}
"""

        try:
            response = self.client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=system_instruction,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SocraticHint,
                    temperature=0.3
                )
            )
            hint = SocraticHint.model_validate_json(response.text)
            hint.hint_level = hint_level
            return hint
        except Exception as e:
            print(f"[SocraticTutorAgent] Hint error ({e}). Returning calibrated fallback.")
            return default_hints.get(hint_level, default_hints[1])
