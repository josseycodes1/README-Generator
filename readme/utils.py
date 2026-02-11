import logging
import re
from .llm import GeminiClient, LLMGenerationError
from .prompts import build_readme_prompt
from .generator import generate_base_readme
from .cache import make_cache_key, get_cached_readme, set_cached_readme

logger = logging.getLogger(__name__)

def generate_readme_markdown_with_llm(analysis_data: dict, repo_url: str) -> str:
    base_readme = generate_base_readme(analysis_data)
    
    cache_key = make_cache_key(repo_url, analysis_data)
    cached = get_cached_readme(cache_key)
    if cached:
        logger.info("Returning cached README from LLM", extra={"request_id": cache_key})
        return cached
    
    prompt = build_readme_prompt(analysis_data, base_readme)
    llm = GeminiClient()
    
    try:
        logger.info("Sending prompt to Gemini", extra={"request_id": cache_key})
        enhanced = llm.generate(prompt, request_id=cache_key)
        logger.info("Received response from Gemini", extra={"request_id": cache_key})
    except LLMGenerationError as e:
        logger.error("Gemini generation failed", extra={"request_id": cache_key})
        raise e
    
    formatted_readme = fix_markdown_paragraphs(enhanced)
    
    final_readme = insert_file_tree(formatted_readme, analysis_data)
    final_readme = ensure_proper_paragraphs(final_readme)
    
    set_cached_readme(cache_key, final_readme)
    logger.info("Cached LLM README", extra={"request_id": cache_key})
    return final_readme

def insert_file_tree(readme_content: str, analysis_data: dict) -> str:
    file_tree = analysis_data.get("readme_assets", {}).get("file_tree", [])
    
    if not file_tree:
        return readme_content
    
    tree_section = "```\n" + "\n".join(file_tree) + "\n```"
    
    placeholder = "*File structure will be shown here*"
    if placeholder in readme_content:
        return readme_content.replace(placeholder, tree_section)
    
    pattern = r"(## 📁 Project Structure\n\n)"
    if re.search(pattern, readme_content):
        return re.sub(pattern, f"\\1{tree_section}\n\n", readme_content)
    
    return readme_content + "\n\n" + "## 📁 Project Structure\n\n" + tree_section

def fix_markdown_paragraphs(content: str) -> str:
    if not content:
        return content
    
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        current_line = lines[i].rstrip()
        
        if i == 0:
            fixed_lines.append(current_line)
            i += 1
            continue
        
        previous_line = lines[i-1].rstrip()
        
        if current_line == '':
            fixed_lines.append('')
            i += 1
            continue
        
        is_special_line = (
            current_line.startswith(('#', '-', '*', '|', '```', '`', '>', '    ', '\t', 
                                   '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '0.')) or
            re.match(r'^\d+\.', current_line)
        )
        
        if is_special_line:
            fixed_lines.append(current_line)
            i += 1
            continue
        
        if previous_line != '' and not previous_line.endswith((':', ';', ',', '-', '—')):
            if not any(previous_line.startswith(x) for x in ['-', '*', '|', '```', '`', '>']):
                if i > 0 and fixed_lines[-1] != '':
                    fixed_lines.append('')
        
        fixed_lines.append(current_line)
        i += 1
    
    return '\n'.join(fixed_lines)

def ensure_proper_paragraphs(content: str) -> str:
    sections = content.split('\n## ')
    if len(sections) <= 1:
        return content
    
    result = sections[0]
    
    for section in sections[1:]:
        if not section.strip():
            continue
        
        lines = section.split('\n')
        if not lines:
            continue
        
        section_title = lines[0]
        section_body = '\n'.join(lines[1:]) if len(lines) > 1 else ''
        
        section_body = re.sub(r'\n{3,}', '\n\n', section_body)
        
        paragraphs = section_body.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            para = para.strip()
            
            if para.startswith(('```', '|', '-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '0.')):
                formatted_paragraphs.append(para)
            else:
                formatted_paragraphs.append(para + '\n')
        
        formatted_body = '\n'.join(formatted_paragraphs)
        
        result += f'\n## {section_title}\n\n{formatted_body}'
    
    return result.strip()