import sys
from pathlib import Path

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini

# Import from common directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "noframework" / "python"))

from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    TECH_WRITER_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args
)
from common.logging import logger, configure_logging
from common.tools import TOOLS_JSON

class ModelFactory:
    VENDOR_MAP = {
        'openai': OpenAIChat,
        'google': Gemini,
    }
    
    @classmethod
    def create(cls, model_name: str, **kwargs):
        if not model_name:
            raise ValueError("Model name cannot be None or empty")
        
        vendor, model_id = model_name.split("/", 1)    
        model_class = cls.VENDOR_MAP.get(vendor)
        return model_class(id=model_id, **kwargs)

def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:
    prompt = read_prompt_file(prompt_file_path)
    model = ModelFactory.create(model_name)

    agent = Agent(
        model=model,
        instructions=TECH_WRITER_SYSTEM_PROMPT,
        tools=TOOLS_JSON,
        markdown=False,  # We want plain text output for consistency
    )
    agent.model.generate_content_config = {"temperature": 0}
    full_prompt = f"Base directory: {directory_path}\n\n{prompt}"
    response = agent.run(full_prompt)
    if hasattr(response, 'content'):
        analysis_result = response.content
    else:
        analysis_result = str(response)
    
    repo_name = Path(directory_path).name
    return analysis_result, repo_name, repo_url or ""

def main():
    try:
        configure_logging()
        args = get_command_line_args()
        repo_url, directory_path = configure_code_base_source(args.repo, args.directory, args.cache_dir)
        analysis_result, repo_name, _ = analyse_codebase(directory_path, args.prompt_file, args.model, args.base_url, repo_url)
        output_file = save_results(analysis_result, args.model, repo_name, args.output_dir, args.extension, args.file_name)
        create_metadata(output_file, args.model, repo_url, repo_name, analysis_result, args.eval_prompt)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()