import os
import subprocess
import tempfile
import shutil
from django.conf import settings


class LaTeXConverter:
    """Convert LaTeX code to PDF"""
    
    @staticmethod
    def latex_to_pdf(latex_code, output_filename):
        """
        Convert LaTeX code to PDF file
        Returns: (success: bool, pdf_path: str or error_message: str)
        """
        # Create temp directory for LaTeX compilation
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Clean LaTeX code before writing
            latex_code = LaTeXConverter._clean_latex(latex_code)
            
            # Write LaTeX code to .tex file
            tex_file_path = os.path.join(temp_dir, 'assignment.tex')
            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(latex_code)
            
            # Run pdflatex once (no need for second run since no TOC)
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'assignment.tex'],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Check if PDF was generated
            pdf_file = os.path.join(temp_dir, 'assignment.pdf')
            if os.path.exists(pdf_file):
                # Create media/temp directory if it doesn't exist
                temp_media_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
                os.makedirs(temp_media_dir, exist_ok=True)
                
                # Move PDF to media/temp with proper filename
                final_pdf_path = os.path.join(temp_media_dir, output_filename)
                shutil.move(pdf_file, final_pdf_path)
                
                return True, final_pdf_path
            else:
                # Extract error from log file
                log_file = os.path.join(temp_dir, 'assignment.log')
                error_message = "PDF generation failed"
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                        # Extract first error
                        if '!' in log_content:
                            error_lines = [line for line in log_content.split('\n') if line.startswith('!')]
                            if error_lines:
                                error_message = error_lines[0]
                
                return False, error_message
        
        except subprocess.TimeoutExpired:
            return False, "LaTeX compilation timeout (>60s)"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @staticmethod
    def _clean_latex(latex_code):
        """Clean LaTeX code to prevent blank pages without affecting title page spacing"""
        # Remove markdown code blocks
        latex_code = latex_code.replace('``````', '').strip()
        
        # Ensure starts with \documentclass
        if '\\documentclass' in latex_code:
            start_idx = latex_code.index('\\documentclass')
            latex_code = latex_code[start_idx:]
        
        # Ensure ends with \end{document}
        if '\\end{document}' in latex_code:
            end_idx = latex_code.index('\\end{document}') + len('\\end{document}')
            latex_code = latex_code[:end_idx]
        
        # Only clean before \begin{document}, not inside the document content
        if '\\begin{document}' in latex_code:
            parts = latex_code.split('\\begin{document}', 1)
            preamble = parts[0]
            body = parts[1] if len(parts) > 1 else ''
            
            # Remove \newpage from preamble only (not from body/title page)
            preamble = preamble.replace('\\newpage', '')
            
            # Remove excessive blank lines from preamble only
            while '\n\n\n' in preamble:
                preamble = preamble.replace('\n\n\n', '\n\n')
            
            # Reconstruct - keep body unchanged
            latex_code = preamble + '\\begin{document}' + body
        
        return latex_code.strip()
    
    @staticmethod
    def sanitize_filename(filename):
        """Remove special characters from filename"""
        # Replace spaces and special chars with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # Remove multiple underscores
        while '__' in filename:
            filename = filename.replace('__', '_')
        return filename.strip('_')
