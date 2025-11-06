import google.generativeai as genai
from django.conf import settings


class GeminiService:
    """Service for interacting with Gemini API"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_latex_solution(self, assignment_text, metadata):
        """Generate LaTeX solution for assignment"""
        prompt = self._build_prompt(assignment_text, metadata)
        
        try:
            response = self.model.generate_content(prompt)
            latex_code = response.text
            
            # Clean the response
            latex_code = self._clean_latex_code(latex_code)
            
            return latex_code
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def retry_with_error(self, previous_latex, error_message):
        """Retry LaTeX generation with error feedback"""
        retry_prompt = f"""
The following LaTeX code generated an error during compilation:

ERROR: {error_message}

LATEX CODE:
{previous_latex}

Please fix the LaTeX code to resolve this error. Return ONLY the corrected LaTeX code, nothing else.
Start with \\documentclass and end with \\end{{document}}. No extra text or markdown.
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
        # Remove markdown code blocks if present
        latex_code = latex_code.replace('``````', '')
        
        # Remove any text before \documentclass
        if '\\documentclass' in latex_code:
            latex_code = latex_code[latex_code.index('\\documentclass'):]
        
        # Remove any text after \end{document}
        if '\\end{document}' in latex_code:
            end_index = latex_code.index('\\end{document}') + len('\\end{document}')
            latex_code = latex_code[:end_index]
        
        # Remove extra newlines at the start
        latex_code = latex_code.lstrip('\n')
        
        return latex_code.strip()
    
    def _build_prompt(self, assignment_text, metadata):
        """Build comprehensive prompt for Gemini with exact title page template"""
        prompt = f"""
You are an expert academic assistant. Generate a complete, properly formatted LaTeX document for the following assignment.

**ASSIGNMENT DETAILS:**
- Subject: {metadata.get('subject_name', 'N/A')}
- Assignment Number: {metadata.get('assignment_number', 'N/A')}
- Submitted to: {metadata.get('tutor_name', 'N/A')}
- Submitted by: {metadata.get('student_name', 'N/A')}
- Registration Number: {metadata.get('registration_number', 'N/A')}
- University: {metadata.get('university_name', 'N/A')}
- Department: {metadata.get('department_name', 'N/A')}

**ASSIGNMENT CONTENT:**
{assignment_text}

**CRITICAL FORMATTING REQUIREMENTS:**
1. Start IMMEDIATELY with \\documentclass{{article}} - no text before this
2. Use the EXACT title page template provided below
3. Do NOT modify the title page structure or spacing
4. After title page, start the solution directly (NO table of contents)
5. Do NOT include \\tableofcontents command
6. You CAN use tabular/table environments for data tables in solutions

**EXACT TITLE PAGE TEMPLATE TO USE:**

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

**CONTENT REQUIREMENTS:**
1. After title page, add \\newpage and start solution section immediately
2. Do NOT include \\tableofcontents
3. Provide comprehensive, detailed solutions with:
   - Clear explanations for each question/problem
   - Step-by-step working where applicable
   - Proper mathematical notation using LaTeX math mode
   - Well-structured sections and subsections
   - Data tables using tabular environment when needed (for showing data/results)
4. Use standard LaTeX packages: geometry, amsmath, graphicx, hyperref, fancyhdr, booktabs (for tables)
5. Ensure all LaTeX syntax is valid and will compile without errors

**OUTPUT FORMAT:**
- Return ONLY the complete LaTeX code
- Start with \\documentclass{{article}}
- Use the exact title page template above (copy it exactly)
- Do NOT add \\tableofcontents command
- End with \\end{{document}}
- Do NOT include markdown formatting, backticks, or explanations

Generate the complete LaTeX document now using the exact title page template provided.
"""
        return prompt
