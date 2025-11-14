import google.generativeai as genai
from django.conf import settings

class GeminiService:
    """Service for interacting with Gemini API"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            generation_config={
                "temperature": 0.6,
                "top_p": 0.85,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
    
    def generate_latex_solution(self, assignment_text, metadata):
        """Generate LaTeX solution for assignment"""
        prompt = self._build_prompt(assignment_text, metadata)
        
        try:
            response = self.model.generate_content(prompt)
            latex_code = response.text
            latex_code = self._clean_latex_code(latex_code)
            return latex_code
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def retry_with_error(self, previous_latex, error_message):
        """Retry LaTeX generation with error feedback"""
        retry_prompt = f"""
The LaTeX code failed compilation. Fix these issues:

ERROR: {error_message}

FAILED CODE:
{previous_latex}

FIX IT BY:
- Removing ANY \\includegraphics or external file references
- Simplifying complex formulas
- Using only: amsmath, geometry, booktabs, fancyhdr
- Ensuring all braces match perfectly

Return ONLY corrected LaTeX starting with \\documentclass and ending with \\end{{document}}.
"""
        try:
            response = self.model.generate_content(retry_prompt)
            latex_code = response.text
            latex_code = self._clean_latex_code(latex_code)
            return latex_code
        except Exception as e:
            raise Exception(f"Gemini retry error: {str(e)}")
    
    def _clean_latex_code(self, latex_code):
        """Clean and validate LaTeX code"""
        latex_code = latex_code.replace('``````', '')
        
        if '\\documentclass' in latex_code:
            latex_code = latex_code[latex_code.index('\\documentclass'):]
        
        if '\\end{document}' in latex_code:
            end_index = latex_code.index('\\end{document}') + len('\\end{document}')
            latex_code = latex_code[:end_index]
        
        return latex_code.strip()
    
    def _build_prompt(self, assignment_text, metadata):
        """Build human-like prompt with your exact title page template"""
        
        prompt = f"""You are a university student completing an assignment. Write naturally with an authentic student voice - confident but conversational, knowledgeable but not robotic.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ASSIGNMENT INFO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Subject: {metadata.get('subject_name', 'N/A')}
Assignment #{metadata.get('assignment_number', 'N/A')}
Tutor: {metadata.get('tutor_name', 'N/A')}
Student: {metadata.get('student_name', 'N/A')}
Reg: {metadata.get('registration_number', 'N/A')}
University: {metadata.get('university_name', 'N/A')}
Department: {metadata.get('department_name', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 QUESTIONS TO ANSWER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{assignment_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 HUMAN WRITING STYLE (Critical):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**FORBIDDEN AI Patterns:**
❌ "involves", "encompasses", "fundamentally"
❌ "Additionally", "Furthermore", "Moreover" at paragraph starts
❌ "In conclusion", "To summarize", "Overall" at end
❌ More than 2 bullet lists in entire document
❌ Perfect grammar everywhere (occasional natural imperfections OK)

**REQUIRED Natural Patterns:**
✅ Vary paragraph starts: "Looking at...", "When we consider...", "What's interesting..."
✅ Use contractions: "it's", "that's", "there's"
✅ Mix sentence lengths drastically
✅ Occasional: "basically", "essentially", "actually"
✅ Personal touches: "From what I understand...", "This makes sense because..."
✅ Active voice 80% of time
✅ Real examples when possible

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 EXACT DOCUMENT STRUCTURE (MUST FOLLOW):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

\\documentclass[12pt, a4paper]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{amsmath, amssymb}}
\\usepackage{{fancyhdr}}
\\usepackage{{booktabs}}
\\usepackage{{enumitem}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\rhead{{{metadata.get('subject_name', 'Assignment')}}}
\\lhead{{Assignment \\#{metadata.get('assignment_number', '1')}}}
\\cfoot{{\\thepage}}

\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{10pt}}

\\begin{{document}}

% ==================== EXACT TITLE PAGE (DO NOT MODIFY) ====================
\\begin{{titlepage}}
    \\centering
    \\vspace*{{2cm}}
    
    {{\\Huge\\bfseries {metadata.get('university_name', 'University')} \\par}}
    \\vspace{{0.8cm}}
    {{\\large Department of {metadata.get('department_name', 'Department')} \\par}}
    
    \\vspace{{2.5cm}}
    
    {{\\Large\\bfseries Assignment \\#{metadata.get('assignment_number', '1')} \\par}}
    \\vspace{{0.3cm}}
    {{\\LARGE\\bfseries {metadata.get('subject_name', 'Subject')} \\par}}
    
    \\vspace{{3cm}}
    
    {{\\large\\textbf{{Subject:}} {metadata.get('subject_name', 'N/A')} \\par}}
    \\vspace{{0.3cm}}
    {{\\large\\textbf{{Assignment Number:}} {metadata.get('assignment_number', 'N/A')} \\par}}
    \\vspace{{0.3cm}}
    {{\\large\\textbf{{Submitted To:}} {metadata.get('tutor_name', 'N/A')} \\par}}
    \\vspace{{0.3cm}}
    {{\\large\\textbf{{Submitted By:}} {metadata.get('student_name', 'N/A')} \\par}}
    \\vspace{{0.3cm}}
    {{\\large\\textbf{{Registration Number:}} {metadata.get('registration_number', 'N/A')} \\par}}
    \\vspace{{0.3cm}}
    {{\\large\\textbf{{Department of:}} {metadata.get('department_name', 'N/A')} \\par}}
    
    \\vfill
    
    {{\\large \\today \\par}}
\\end{{titlepage}}

\\newpage

% ==================== SOLUTIONS START HERE ====================

[For EACH question, use this structure:]

\\section*{{Question [Number]}}

\\textit{{[Brief one-sentence restatement of the question]}}

\\vspace{{6pt}}

[Write 3-5 natural paragraphs following these patterns:]

**Opening Paragraph:**
- Start naturally: "When we look at [topic]...", "To understand this...", "What's important here is..."
- NO textbook definitions like "X is defined as..."
- Mix short and long sentences

**Body Paragraphs (2-3):**
- Explain conversationally like teaching a friend
- Use "basically", "essentially", "really" occasionally
- Include brief examples: "For instance...", "Looking at..."
- Vary transitions: "Now", "What happens next", "This ties into"
- ONE itemize list maximum (2-4 items), rest as prose
- Math inline: \\(x = 5\\) or display: \\[E = mc^2\\]
- Tables ONLY for actual data comparison (use sparingly):
  \\begin{{center}}
  \\begin{{tabular}}{{lcc}}
  \\toprule
  Item & Value & Unit \\\\
  \\midrule
  Data & 100 & kg \\\\
  \\bottomrule
  \\end{{tabular}}
  \\end{{center}}

**Closing naturally:**
- NO "thus", "therefore", "in conclusion" at end of answers
- Just finish explaining naturally when done
- Move to next question

\\vspace{{12pt}}

% ==================== CRITICAL RULES ====================
After last question's answer:
- DO NOT add conclusion section
- DO NOT add summary section
- DO NOT add "Thank you" or closing remarks
- Simply end with: \\end{{document}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 ABSOLUTE TECHNICAL RESTRICTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- NO \\includegraphics, NO images, NO external files
- NO tikz, pgfplots, gantt, diagrams
- NO \\tableofcontents command
- NO complex packages beyond: amsmath, geometry, booktabs, fancyhdr, enumitem
- Must compile in <30 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ QUALITY CHECKLIST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Sounds like a real student (not AI/ChatGPT)
[ ] Sentence lengths vary wildly (5-30 words)
[ ] NO "X is a concept that..." openings
[ ] Contractions used naturally
[ ] Some "basically"/"essentially" included
[ ] NO "Additionally"/"Furthermore" starts
[ ] NO conclusion/summary section
[ ] Maximum 2 bullet lists total
[ ] Personal voice present
[ ] Ends naturally without wrapping up
[ ] Title page EXACTLY matches template above

Generate the COMPLETE LaTeX document now. Return ONLY pure LaTeX code starting with \\documentclass and ending with \\end{{document}}. NO markdown, NO explanations, NO text before or after.
"""
        return prompt
