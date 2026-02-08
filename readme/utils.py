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
    final_readme = ensure_double_newlines(final_readme)
    
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
    
    pattern = r"(##  Project Structure\n\n)"
    if re.search(pattern, readme_content):
        return re.sub(pattern, f"\\1{tree_section}\n\n", readme_content)
    
    return readme_content + "\n\n" + "##  Project Structure\n\n" + tree_section

def fix_markdown_paragraphs(content: str) -> str:
    if not content:
        return content
    
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        current_line = line.rstrip()
        
        if i == 0:
            fixed_lines.append(current_line)
            continue
        
        previous_line = lines[i-1].rstrip()
        
        if current_line == '' or previous_line == '':
            fixed_lines.append(current_line)
            continue
        
        if current_line.startswith(('#', '-', '*', '1.', '|', '```', '`', '>', '    ', '\t')):
            fixed_lines.append(current_line)
            continue
        
        if previous_line.endswith(('.', '!', '?', ':', ';', ')', ']', '}')):
            if not previous_line.startswith(('#', '-', '*', '1.', '|', '```', '`', '>', '    ', '\t')):
                fixed_lines.append('')
        
        fixed_lines.append(current_line)
    
    return '\n'.join(fixed_lines)

def ensure_double_newlines(content: str) -> str:
    sections = re.split(r'(## .+?\n)', content)
    
    if len(sections) < 2:
        return content
    
    result = sections[0]
    
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            header = sections[i]
            body = sections[i + 1]
            
            body = re.sub(r'(\n{3,})', '\n\n', body)
            
            body_lines = body.strip().split('\n')
            formatted_body = []
            
            for line in body_lines:
                if line.strip() == '':
                    if formatted_body and formatted_body[-1] != '':
                        formatted_body.append('')
                else:
                    formatted_body.append(line)
            
            body = '\n'.join(formatted_body)
            
            if body and not body.startswith('\n'):
                body = '\n' + body
            
            result += header + body
    
    return result.rstrip() + '\n'