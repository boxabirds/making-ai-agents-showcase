#!/usr/bin/env python3
"""
Tech Writer Agent using Google ADK
Direct port of baseline/tech-writer.py to use ADK framework
"""

import asyncio
import sys
from pathlib import Path
from typing import List
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

# Add baseline to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "baseline"))

# Import from common modules - reuse everything possible
from common.utils import (
    REACT_SYSTEM_PROMPT,
    read_prompt_file,
    save_results,
    create_metadata,
    configure_code_base_source,
    get_command_line_args,
    
)
from common.tools import TOOLS_JSON 
from common.logging import logger, configure_logging

async def stupid_adk_hack_to_get_model(vendor_model_id_combo):
    # This feels like marketing getting in the way of clean API design
    # openrouter and liteLLM both support <vendor>/<model id> but does ADK? 
    # CONDITIONALLY

    vendor, model_id = vendor_model_id_combo.split("/", 1)
    if vendor == "google":
        # Gemini models can be used directly without vendor prefix
        # Yeah this is some crappy DevUX for sure
        return model_id
    else:
        # Non-Google models need LiteLLM wrapper with full vendor/model string
        return LiteLlm(model=vendor_model_id_combo)


async def analyse_codebase(directory_path: str, prompt_file_path: str, vendor_model_id_combo: str, repo_url: str = None) -> tuple[str, str, str]:
    prompt = read_prompt_file(prompt_file_path)
    
    model = await stupid_adk_hack_to_get_model(vendor_model_id_combo)
    tech_writer_agent = Agent(
        name="tech_writer",
        model=model,
        instruction=REACT_SYSTEM_PROMPT,
        description="A technical documentation agent that analyzes codebases using ReAct pattern",
        tools=list(TOOLS_JSON.values()),
        generate_content_config=types.GenerateContentConfig(
            temperature=0,  # Use 0 for "more deterministic 😉"
        )
    )
    
    # ADK uses runners to manage agent execution and state persistence
    # InMemoryRunner stores conversation history and artifacts in memory (lost on exit)
    runner = InMemoryRunner(agent=tech_writer_agent, app_name='tech_writer')
    
    # Sessions track conversations and state for a specific user
    # user_id identifies who is running the agent (used for multi-user scenarios)
    # In our CLI tool, we use a fixed 'cli_user' since it's single-user
    session = await runner.session_service.create_session(
        app_name='tech_writer',
        user_id='cli_user'
    )
    
    # Prepare the full prompt with directory context
    full_prompt = f"Base directory: {directory_path}\n\n{prompt}"
    
    # Create user content
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(text=full_prompt)]
    )
    
    logger.info("Running analysis...")
    full_response = ""
    # run_async requires both user_id and session_id to:
    # - user_id: groups sessions by user (for organizing multi-user scenarios)
    # - session_id: links to a specific conversation's history and state
    # The session stores tool results, conversation context, and agent memory
    async for event in runner.run_async(
        user_id='cli_user',
        session_id=session.id,
        new_message=content
    ):
        if event.content.parts and event.content.parts[0].text:
            full_response += event.content.parts[0].text
    
    # Get repository name for output file
    repo_name = Path(directory_path).name
    
    return full_response, repo_name, repo_url or ""


async def main():
    try:
        configure_logging()
        args = get_command_line_args()
        
        # Configure codebase source (repo or directory)
        repo_url, directory_path = configure_code_base_source(args.repo, args.directory, args.cache_dir)
            
        analysis_result, repo_name, _ = await analyse_codebase(
            directory_path, 
            args.prompt_file, 
            args.model, 
            repo_url
        )
        
        # Save the results
        output_file = save_results(analysis_result, args.model, repo_name, args.output_dir, args.extension, args.file_name)
        logger.info(f"Analysis complete. Results saved to: {output_file}")
        
        # Always create metadata (with optional evaluation)
        create_metadata(output_file, args.model, repo_url, repo_name, analysis_result, args.eval_prompt)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())