# Tech Writer Agent in 7 different frameworks

So you want to make an agent.   
**How useful are agent frameworks anyway?**   
In a [past issue of Making AI Agents](https://makingaiagents.substack.com/p/i-built-an-agent-from-scratch-to), I wrote a tech writer agent without a framework.   
This "no framework" agent showed how simple agents can be, yet still have quite magical properties that were sci-fi just a few years back.   
To answer the framework question, I implemented the exact same tech writer agent in a selection of different frameworks, and share my insights here. 

## But first, how many agent maker frameworks are there?

At last count I have identified approximately:

* 133 agent maker solutions  
* 46 of which are open source  
* 32 of those are in python  
* 15 of those are python packages (while the rest run on dedicated servers)

So far, I have rewritten the tech writer agent seven different frameworks:

* Agent Developer Toolkit (Google)  
* Agno  
* Atomic Agents  
* Autogen (Microsoft)  
* DSPy  
* Langgraph  
* Pydantic-AI

## Why did you pick the tech writer agent for evaluation?

The tech writer agent **answers plain-English questions about a github repo**. 

You **give it a brief**, and it will **produce a report**. 

It solves the problem of how to answer a wide range of questions without needing to create different tools. E.g

* Architect: **give me an overview of the code base**  
* New starter: **give me a new starter guide**  
* Release engineering: **what is involved in deploying this code?** 

These all can be answered by the same agent: **in the past they'd have required quite different and complex scripts**, or a lot of eyeball time.

So the tech writer agent is a **great combination of being both very simple, and very useful**. 

## What did I learn?

For a simple agent like my tech writer, the agent frameworks are useful, but not essential. 

Their power may come into play with more complex scenarios such as interactive chat or multi-agent support, which I'll cover in future issues of Making AI Agents. 

To explain my choices, let me go back to the essential components of an agent.

There are 3 essential building blocks of an agent:

* The language model  
* Tools it calls  
* Memory

As such, a good agent framework makes light work of these 3 things:

* **Language model**: the right language model depends on the use case: they are not set and forget. **How easy is it to switch models?**   
* **Tools**: ideally I just point the agent at my python functions. **Can I use everyday python functions with no fuss?**  
* **Memory**: unless it's unavoidable, I shouldn't have to worry about how the agent remembers its actions. **Do I have to be bothered with how the agent manages its memory?**

When agents answer these three questions well, they also require less code to write.   
To this end, of the 7 I initially chose, standout agent makers were **DSPy** and **Agno**, both being very compact and flexible. 

## What did I standardise on?

A rule that in the end added a smidge of complexity to every agent was a firm rule: **"use the common functions and constants wherever possible".** 

See, I had this idea that it would be fairer to the frameworks by having a few standard things:

* Standard prompts  
* Standard tools

This turned out to be a mixed blessing:

* Input and output formats did vary a bit, so sometimes an agent would need to do a bit more wrapping than perhaps would normally be required  
* It did however ensure that the complex functionality of .gitignore-enabled hierarchical file search worked consistently, and that the prompts were the same (mostly)

Also I standardised on execution: they all use uv, the new hotness when it comes to python package management. Uv was the right choice: it's ultra fast and made it easy to create isolated agent environments to avoid any potential conflicts. 

## How did I rank them?

All the frameworks have their pros and cons. 

While I tested the frameworks with a very simple use case, it was enough to get a feel for the design philosophies each had. 

On one end you have "as terse as possible", and on the other you have "as type-safe as possible". (My personal opinion is "as terse as possible" is more idiomatic of python.)

I broke out the seven I evaluated into four broad groups:

* Ultra low friction  
* Low friction  
* Perfectly acceptable   
* Higher friction

Are any really bad? They're all mostly harmless, except I found Atomic Agents type-safe verbosity something I'd not want to repeat.   
Where does the value of these frameworks come in then, for my use case? 

### Ultra-low friction

* DSPy 2.6.17: super concise.   
* Agno 1.5.10: compact; could be even more so

### Low friction

* Autogen 0.6.1: hard-coded LLM supoprt

### Perfectly acceptable

* Google ADK 0.1.0: Google bias harms it  
* LangGraph 0.4.8: complex tool definitions  
* Pydantic-AI 0.2.16b: complex tool definitions

### Higher friction

* Atomic Agents: overengineered for my use case

# Google Agent Developer Kit

At around 115 lines, this is a good, concise framework to work with:

* It's compact and optionally has server capabilities for running the agent as a server with visual tools.   
* Part of a larger visual / server solution: while it can be run in isolation without a server, it's clearly intended by default to be run as a server. It is also a response to Microsoft's Autogen, offering a very powerful web-based studio tool., I expect significant work to happen on this in the coming quarters, possibly further integrated with other tools  in Google's Dev ecosystem (like [aistudio.google.com](http://aistudio.google.com), [jules.google](https://jules.google), and various others).   
* Note also that about 10 lines of the agent was comments I thought necessary to help with the new concepts ADK presents. 

Downsides are slight:

* Annoying: it doesn't have a standard way to access language models: it has one way for Gemini and one for all others, hence my "stupid\_hack\_to\_get\_model()" function. To me this just adds unecessary friction.   
* It is slightly more complex in that it needs the concept of a session, which holds memory. This is in contrast to many other agents that encapsulate it away entirely. I respect this abstraction but given for my use case there was no real need to use these concepts other than to pass them back to more ADK APIs, there could be merit in considering a higher level offering that doesn't need sessions or user ids.

## ADK Tech Writer Agent Code

```python
import asyncio
import sys
from pathlib import Path
from typing import List
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

# Add noframework/python to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "noframework" / "python"))

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

    vendor, model_id = vendor_model_id_combo.split("/", 1)
    if vendor == "google":
        # Gemini models can be used directly without vendor prefix
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
    
    full_prompt = f"Base directory: {directory_path}\n\n{prompt}"
    
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
    
    repo_name = Path(directory_path).name
    
    return full_response, repo_name, repo_url or ""

async def main():
    try:
        configure_logging()
        args = get_command_line_args()
        
        repo_url, directory_path = configure_code_base_source(args.repo, args.directory, args.cache_dir)
            
        analysis_result, repo_name, _ = await analyse_codebase(
            directory_path, 
            args.prompt_file, 
            args.model, 
            repo_url
        )
        
        output_file = save_results(analysis_result, args.model, repo_name, args.output_dir, args.extension, args.file_name)
        logger.info(f"Analysis complete. Results saved to: {output_file}")
        
        create_metadata(output_file, args.model, repo_url, repo_name, analysis_result, args.eval_prompt)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

# Agno

Clocking in at 72 lines Agno is by far the most compact and cleanest implementation of my tech writer agent. 

It could also be made even more compact if it had a universal way to instantiate a language model using the emergent format that many frameworks and tools support, specifying vendor and model id separated by a slash or colon e.g. "openai:gpt-4.1-mini" or "anthropic/claude-sonnet-4.0", such as supported by LangChain, LiteLLM, and OpenRouter (to name a few).

As it stands, Agno requires specific class usage for each vendor, and as my code has a string as input, I have a ModelFactory wrapper to do this hackery directly. 

Why did Agno do this? I think there's a misunderstanding here about how language models are used. 

They are absolutely not a set-and-forget solution: business-as-usual with AI engineering is to evaluate a range of models for a given use case, so having a set of different models from different vendors is absolutely normal. It's rare  I find myself committing solidly to a particular language model at all – even operationally I might want to bac

## Agno Tech Writer Code

```python
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
```

# Atomic Agents

This is by far the highest friction framework, clocking in at around 224 lines, which is ironic given one of its biggest selling points is being "extremely lightweight". 

It leans heavily on Instructor and Pydantic, two very respectable frameworks to help type safety and data integrity, and to that end I respect their approach. 

However, writing the agent, it was absolutely the highest friction approach, for instance  needing separate classes for a single tool specification. 

Honestly there's a point where this really starts feeling like it's moving away from Python idioms to something heavier-weight like Java.  
The other big hassle was its fragmentation of prompts into separate aspects, which felt like busywork as ultimately it just stitches it all back together into one piece of text. If you want strongly-typed inputs and outputs, take a look at DSPy which does this very elegantly and compactly. 

## Atomic Agents Tech Writer Agent Code

```python
import sys  
import instructor  
import json  
from pathlib import Path  
from pydantic import Field  
  
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema  
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase  
from atomic_agents.lib.components.agent_memory import AgentMemory  
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig  
  
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "noframework" / "python"))  
from common.utils import (  
    read_prompt_file,  
    save_results,  
    create_metadata,  
    ROLE_AND_TASK,  
    GENERAL_ANALYSIS_GUIDELINES,  
    INPUT_PROCESSING_GUIDELINES,  
    CODE_ANALYSIS_STRATEGIES,  
    QUALITY_REQUIREMENTS,  
    REACT_PLANNING_STRATEGY,  
    configure_code_base_source,  
    get_command_line_args,  
    CustomEncoder  
)  
from common.logging import logger, configure_logging  
from common.tools import TOOLS  
  
class TechWriterInputSchema(BaseIOSchema):  
    """Input schema for the tech writer agent."""  
    prompt: str = Field(..., description="The analysis prompt")  
    directory: str = Field(..., description="Base directory path to analyze")  
  
class TechWriterOutputSchema(BaseIOSchema):  
    """Output schema for the tech writer agent."""  
    analysis_result: str = Field(..., description="The final analysis result")  
  
class CodebaseContextProvider(SystemPromptContextProviderBase):  
    def __init__(self, title: str):  
        super().__init__(title=title)  
        self.base_directory = None  
        self.analysis_prompt = None  
      
    def get_info(self) -> str:  
        return f"Base directory: {self.base_directory}\n\nAnalysis prompt: {self.analysis_prompt}"  
  
class FindAllMatchingFilesInputSchema(BaseIOSchema):  
    """Input schema for finding matching files."""  
    directory: str = Field(..., description="Directory to search in")  
    pattern: str = Field(default="*", description="File pattern to match (glob format)")  
    respect_gitignore: bool = Field(default=True, description="Whether to respect .gitignore patterns")  
    include_hidden: bool = Field(default=False, description="Whether to include hidden files and directories")  
    include_subdirs: bool = Field(default=True, description="Whether to include files in subdirectories")  
  
class FindAllMatchingFilesOutputSchema(BaseIOSchema):  
    """Output schema for finding matching files."""  
    result: str = Field(..., description="JSON string containing list of matching file paths")  
  
class FindAllMatchingFilesTool(BaseTool):  
    """Tool for finding files matching a pattern while respecting .gitignore."""  
    input_schema = FindAllMatchingFilesInputSchema  
    output_schema = FindAllMatchingFilesOutputSchema  
      
    def __init__(self, config: BaseToolConfig = None):  
        super().__init__(config or BaseToolConfig(  
            title="FindAllMatchingFilesTool",  
            description="Find files matching a pattern while respecting .gitignore"  
        ))  
      
    def run(self, params: FindAllMatchingFilesInputSchema) -> FindAllMatchingFilesOutputSchema:  
        logger.info(f"FindAllMatchingFilesTool invoked with directory={params.directory}, pattern={params.pattern}")
        try:  
            tool_func = TOOLS["find_all_matching_files"]  
            result = tool_func(  
                directory=params.directory,  
                pattern=params.pattern,  
                respect_gitignore=params.respect_gitignore,  
                include_hidden=params.include_hidden,  
                include_subdirs=params.include_subdirs,  
                return_paths_as="str"  
            )  
            return FindAllMatchingFilesOutputSchema(result=json.dumps(result, cls=CustomEncoder, indent=2))  
        except Exception as e:  
            return FindAllMatchingFilesOutputSchema(result=f"Error finding files: {str(e)}")  
  
class FileReaderInputSchema(BaseIOSchema):  
    """Input schema for reading file contents."""  
    file_path: str = Field(..., description="Path to the file to read")  
  
class FileReaderOutputSchema(BaseIOSchema):  
    """Output schema for reading file contents."""  
    result: str = Field(..., description="JSON string containing file content or error message")  
  
class FileReaderTool(BaseTool):  
    """Tool for reading the contents of a file."""  
    input_schema = FileReaderInputSchema  
    output_schema = FileReaderOutputSchema  
      
    def __init__(self, config: BaseToolConfig = None):  
        super().__init__(config or BaseToolConfig(  
            title="FileReaderTool",  
            description="Read the contents of a file"  
        ))  
    def run(self, params: FileReaderInputSchema) -> FileReaderOutputSchema:  
        logger.info(f"FileReaderTool invoked with file_path={params.file_path}")
        try:  
            tool_func = TOOLS["read_file"]  
            result = tool_func(params.file_path)  
            return FileReaderOutputSchema(result=json.dumps(result, cls=CustomEncoder, indent=2))  
        except Exception as e:  
            return FileReaderOutputSchema(result=f"Error reading file: {str(e)}")  
  
def create_system_prompt_generator():  
    """Create system prompt generator using existing constants."""  
    background_lines = [  
        line.strip() for line in ROLE_AND_TASK.strip().split('\n') if line.strip()  
    ] + [  
        line.strip() for line in GENERAL_ANALYSIS_GUIDELINES.strip().split('\n')  
        if line.strip() and not line.strip().startswith('Follow these guidelines:') and line.strip() != '-'  
    ]  
      
    strategy = REACT_PLANNING_STRATEGY  
    steps = [  
        line.strip() for line in strategy.strip().split('\n')  
        if line.strip() and (line.strip().startswith(('1.', '2.', '3.', '4.', '5.')))  
    ] + [  
        line.strip() for line in CODE_ANALYSIS_STRATEGIES.strip().split('\n')  
        if line.strip() and line.strip().startswith('-')  
    ]  
      
    output_instructions = [  
        line.strip() for line in INPUT_PROCESSING_GUIDELINES.strip().split('\n')  
        if line.strip() and line.strip().startswith('-')  
    ] + [  
        line.strip() for line in QUALITY_REQUIREMENTS.strip().split('\n')  
        if line.strip()  
    ]  
      
    return SystemPromptGenerator(  
        background=background_lines,  
        steps=steps,  
        output_instructions=output_instructions  
    )  
  
class TechWriterAgent:  
    def __init__(self, vendor_model: str = "openai/gpt-4o-mini"):  
        """Initialize the TechWriter agent with atomic-agents using LiteLLM."""  
          
        import litellm
        client = instructor.from_litellm(litellm.completion)  
          
        self.tools = [FindAllMatchingFilesTool(), FileReaderTool()]  
          
        self.codebase_context = CodebaseContextProvider("Codebase Analysis Context")  
          
        system_prompt_generator = create_system_prompt_generator()  
        system_prompt_generator.context_providers["codebase_context"] = self.codebase_context  

        self.agent = BaseAgent(  
            BaseAgentConfig(  
                client=client,  
                model=vendor_model,  
                system_prompt_generator=system_prompt_generator,  
                input_schema=TechWriterInputSchema,  
                output_schema=TechWriterOutputSchema,  
                memory=AgentMemory(),  
                model_api_parameters={"temperature": 0},  
                tools=self.tools,
                max_tool_iterations=50 
            )  
        )  
      
    def run(self, prompt: str, directory: str) -> str:  
        self.codebase_context.base_directory = directory  
        self.codebase_context.analysis_prompt = prompt  
          
        input_data = TechWriterInputSchema(prompt=prompt, directory=directory)  
        
        logger.info(f"Running agent with {len(self.tools)} tools")
        for tool in self.tools:
            logger.info(f"Tool: {tool.__class__.__name__}")
        
        result = self.agent.run(input_data)  
          
        return result.analysis_result  
  
def analyse_codebase(directory_path: str, prompt_file_path: str, vendor_model: str,  
                    base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:  
    # TODO base_url support not needed -- it's only required for ollama
    prompt = read_prompt_file(prompt_file_path)  
    agent = TechWriterAgent(vendor_model)  
    analysis_result = agent.run(prompt, directory_path)  
      
    repo_name = Path(directory_path).name  
    return analysis_result, repo_name, repo_url or ""  
  
def main():  
    try:  
        configure_logging()  
        args = get_command_line_args()  
        repo_url, directory_path = configure_code_base_source(  
            args.repo, args.directory, args.cache_dir  
        )  
          
        analysis_result, repo_name, _ = analyse_codebase(  
            directory_path, args.prompt_file, args.model, args.base_url, repo_url  
        )  
          
        output_file = save_results(  
            analysis_result, args.model, repo_name, args.output_dir, args.extension, args.file_name  
        )  
        logger.info(f"Analysis complete. Results saved to: {output_file}")  
          
        create_metadata(  
            output_file, args.model, repo_url, repo_name, analysis_result, args.eval_prompt  
        )  
          
    except Exception as e:  
        logger.error(f"Error: {str(e)}", exc_info=True)  
        sys.exit(1)  
  
if __name__ == "__main__":  
    main()
```

# Autogen

At 124 lines, this was a middle-of the road implementation.   
Autogen  was actually one of the first agent frameworks, and it has a very comprehensive Autogen Studio too which I covered briefly in a past issue. 

Its LLM implementation relies entirely on a vendor supporting the OpenAI API protocol (which almost all do), with an unfortunate restriction to a subset that it specifically lists. 

Relying on OpenAI's API is a completely reasonable thing to do and I'd love to see it open up to be more flexible to support other models and vendors too. 

Finally, its tool support is fairly lightweight too; I only had to add async wrappers to the tools, which otherwise just worked.

## Autogen Tech Writer Agent Code

```python
import sys
from pathlib import Path
from typing import List, Dict, Any
from autogen_agentchat.agents import AssistantAgent

from autogen_ext.models.openai import OpenAIChatCompletionClient
import argparse

# Add the noframework/python directory to sys.path to import common modules
noframework_path = Path(__file__).parent.parent.parent / "noframework" / "python"
sys.path.insert(0, str(noframework_path))

from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    TECH_WRITER_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args,
    MAX_ITERATIONS,
)

from common.tools import find_all_matching_files, read_file
from common.logging import logger, configure_logging

async def find_all_matching_files_async(
    directory: str, 
    pattern: str = "*", 
    respect_gitignore: bool = True, 
    include_hidden: bool = False,
    include_subdirs: bool = True
) -> List[str]:
    return find_all_matching_files(
        directory=directory,
        pattern=pattern,
        respect_gitignore=respect_gitignore,
        include_hidden=include_hidden,
        include_subdirs=include_subdirs,
        return_paths_as="str"
    )

async def read_file_async(file_path: str) -> Dict[str, Any]:
    return read_file(file_path)

async def analyze_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None, max_iters = MAX_ITERATIONS) -> tuple[str, str, str]:
    prompt = read_prompt_file(prompt_file_path)
    
    # Autogen relies 100% on OpenAI-compatible endpoints, which is most of them
    # but it does have a hard-coded list of models that limits things a bit  
    # default string sent is openai/gpt-4.1-mini which is SOTA cheap model currently
    _, model_id = model_name.split("/", 1)
    
    model_client = OpenAIChatCompletionClient(
        model=model_id,
    )
  
    agent = AssistantAgent(
        name="tech_writer",
        model_client=model_client,
        tools=[find_all_matching_files_async, read_file_async],
        system_message=TECH_WRITER_SYSTEM_PROMPT,
        reflect_on_tool_use=True
    )
    
    task_message = f"Base directory: {directory_path}\n\n{prompt}"
    result = await agent.run(task=task_message)
    analysis_result = result.messages[-1].content
        
    repo_name = Path(directory_path).name
    return analysis_result, repo_name, repo_url or ""

def main():
    import asyncio
    async def async_main():
        try:
            configure_logging()
            args = get_command_line_args()
            
            repo_url, directory_path = configure_code_base_source(
                args.repo, args.directory, args.cache_dir
            )
            
            analysis_result, repo_name, _ = await analyze_codebase(
                directory_path, 
                args.prompt_file, 
                args.model, 
                args.base_url, 
                repo_url,
                getattr(args, 'max_iters', MAX_ITERATIONS)
            )
            
            output_file = save_results(
                analysis_result, args.model, repo_name, 
                args.output_dir, args.extension, args.file_name
            )
            logger.info(f"Analysis complete. Results saved to: {output_file}")
            
            create_metadata(
                output_file, args.model, repo_url, repo_name, 
                analysis_result, getattr(args, 'eval_prompt', None)
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            sys.exit(1)
    
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
```


# DSPy

I place DSPy among the top of my rankings, which is quite remarkable given it's not first and foremost a dedicated agent framework, per se.  
   
It is unusual in that, unlike the others, it's not "just an LLM wrapper". 

It has a completely novel approach to specifying prompts that later, with operational data, can be optimised using very sophisticated optimisation techniques.   
Clocking in at 99 lines this is a very compact solution because:

* It can use any python function as a tool directly  
* It uses LiteLLM for LLM instantiation, so it accepts "\<vendor\>/\<model id\>" combos directly  
* Like Atomic Agents, it has typed input and outputs using Pydantic under the hood, but also manages to be extremely terse.  
* It has a ReAct agent built-in

The only point of friction is what I consider bordering on "docstring abuse": DSPy uses docstrings as a functional source of prompts. 

This might look nice, but actually a) docstrings are not functional parts of the code and really should *only* be used to document behaviour and b) as a result it's a bit of a hack to use external variables as prompts.

To this end, 25 lines of the file is a duplication of the prompts defined in my common utils. An alternative implementation would do this:

 `class.__doc__ = <TECH_WRITER_SYSTEM_PROMPT>` 

… but this is hacky, and if you're looking at it as a normal DSPy program, you might wonder why it has no prompt. 

## DSPy Tech Writer Agent Code
```python
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add noframework/python to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "noframework" / "python"))

import dspy
from common.utils import (
    get_command_line_args,
    read_prompt_file,
    save_results,
    create_metadata,
    configure_code_base_source,
    logger,
    CustomEncoder,
)
from common.tools import TOOLS

class TechWriterSignature(dspy.Signature):
    """
    You are an expert tech writer that helps teams understand codebases with accurate and concise supporting analysis and documentation. 
    Your task is to analyse the local filesystem to understand the structure and functionality of a codebase.

     Follow these guidelines:
    - Use the available tools to explore the filesystem, read files, and gather information.
    - Make no assumptions about file types or formats - analyse each file based on its content and extension.
    - Focus on providing a comprehensive, accurate, and well-structured analysis.
    - Include code snippets and examples where relevant.
    - Organize your response with clear headings and sections.
    - Cite specific files and line numbers to support your observations.

    Important guidelines:
    - The user's analysis prompt will be provided in the initial message, prefixed with the base directory of the codebase (e.g., "Base directory: /path/to/codebase").
    - Analyse the codebase based on the instructions in the prompt, using the base directory as the root for all relative paths.
    - Make no assumptions about file types or formats - analyse each file based on its content and extension.
    - Adapt your analysis approach based on the codebase and the prompt's requirements.
    - Be thorough but focus on the most important aspects as specified in the prompt.
    - Provide clear, structured summaries of your findings in your final response.
    - Handle errors gracefully and report them clearly if they occur but don't let them halt the rest of the analysis.

    When analysing code:
    - Start by exploring the directory structure to understand the project organisation.
    - Identify key files like README, configuration files, or main entry points.
    - Ignore temporary files and directories like node_modules, .git, etc.
    - Analyse relationships between components (e.g., imports, function calls).
    - Look for patterns in the code organisation (e.g., line counts, TODOs).
    - Summarise your findings to help someone understand the codebase quickly, tailored to the prompt.

    When you've completed your analysis, provide a final answer in the form of a comprehensive Markdown document 
    that provides a mutually exclusive and collectively exhaustive (MECE) analysis of the codebase using the user prompt.

    Your analysis should be thorough, accurate, and helpful for someone trying to understand this codebase.

    """

    # TODO the prompt above is a copy of the master prompt in TECH_WRITER_SYSTEM_PROMPT so if that changes, this has to be updated manually
    
    prompt: str = dspy.InputField(desc="The analysis prompt and base directory")
    analysis: str = dspy.OutputField(desc="Comprehensive markdown analysis of the codebase")

def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:
    dspy.configure(lm=dspy.LM(model=model_name))
    
    prompt_content = read_prompt_file(prompt_file_path)
    full_prompt = f"Base directory for analysis: {directory_path}\n\n{prompt_content}"
    
    logger.info(f"Starting DSPy ReAct tech writer with model: {model_name}")
    logger.info(f"Analyzing directory: {directory_path}")
    
    react_agent = dspy.ReAct(TechWriterSignature, tools=list(TOOLS.values()), max_iters=20)
    result = react_agent(prompt=full_prompt)
    analysis = result.analysis
    
    repo_name = Path(directory_path).name
    return analysis, repo_name, repo_url or ""

def main():
    try:
        from common.logging import configure_logging
        configure_logging()
        args = get_command_line_args()
        repo_url, directory_path = configure_code_base_source(args.repo, args.directory, args.cache_dir)
            
        analysis_result, repo_name, _ = analyse_codebase(directory_path, args.prompt_file, args.model, args.base_url, repo_url)

        output_file = save_results(analysis_result, args.model, repo_name, args.output_dir, args.extension, args.file_name)
        logger.info(f"Analysis complete. Results saved to: {output_file}")

        create_metadata(output_file, args.model, repo_url, repo_name, analysis_result, args.eval_prompt)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

# Langgraph

At around 155 lines, this is another decent framework that keeps things simple for the tech writer use case because:

* It has a ReAct agent built-in  
* It supports vendor/model configuration strings

Tools could be lower friction though. 

Honestly my python isn't good enough to understand why it's a problem, but unlike most other frameworks, Langgraph tools have extra complexity around the context in which a tool operates. 

This translates to what amounts to a fairly lightweight wrapper to pass the directory being scanned. 

I really tried to understand why Langgraph couldn't figure this out directly like other frameworks, but left it as-is. 

Maybe a proper python practitioner or Langgraph expert can improve this.

## Langgraph Tech Writer Agent Code
```python
from pathlib import Path
import sys
from typing import Tuple, List, Dict, Any

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage

# Add noframework/python to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "noframework" / "python"))

from common.tools import find_all_matching_files, read_file
from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    TECH_WRITER_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args,
    MAX_ITERATIONS,
    vendor_model_with_colons
)

from common.logging import logger, configure_logging

async def analyze_codebase(
    directory_path: str, 
    prompt_file_path: str, 
    model_name: str, 
    base_url: str = None, 
    repo_url: str = None,
    max_iterations: int = MAX_ITERATIONS
) -> Tuple[str, str, str]:
    prompt = read_prompt_file(prompt_file_path)
    
    def find_files(pattern: str = "*", respect_gitignore: bool = True, 
                   include_hidden: bool = False, include_subdirs: bool = True) -> List[str]:
        return find_all_matching_files(
            directory=directory_path,  
            pattern=pattern,
            respect_gitignore=respect_gitignore,
            include_hidden=include_hidden,
            include_subdirs=include_subdirs,
            return_paths_as="str"
        )
    
    def read_file_with_path_resolution(file_path: str) -> Dict[str, Any]:
        if not Path(file_path).is_absolute():
            file_path = str(Path(directory_path) / file_path)
        return read_file(file_path)
    
    agent = create_react_agent(
        model=vendor_model_with_colons(model_name),
        tools=[find_files, read_file_with_path_resolution],
    )
    
    messages = [
        SystemMessage(content=TECH_WRITER_SYSTEM_PROMPT),
        HumanMessage(content=f"Base directory: {directory_path}\n\n{prompt}")
    ]
    
    result = agent.invoke(
        {"messages": messages},
        config={"recursion_limit": max_iterations}
    )
    
    final_message = result["messages"][-1]
    analysis_result = final_message.content
    
    repo_name = Path(directory_path).name
    return analysis_result, repo_name, repo_url or ""

def main():
    import asyncio
    
    async def async_main():
        try:
            configure_logging()
            args = get_command_line_args()
            
            repo_url, directory_path = configure_code_base_source(
                args.repo, args.directory, args.cache_dir
            )
            
            analysis_result, repo_name, _ = await analyze_codebase(
                directory_path, 
                args.prompt_file, 
                args.model, 
                args.base_url, 
                repo_url,
                getattr(args, 'max_iters', MAX_ITERATIONS)
            )
            
            output_file = save_results(
                analysis_result, args.model, repo_name, 
                args.output_dir, args.extension, args.file_name
            )
            logger.info(f"Analysis complete. Results saved to: {output_file}")
            
            create_metadata(
                output_file, args.model, repo_url, repo_name, 
                analysis_result, getattr(args, 'eval_prompt', None)
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            sys.exit(1)
    
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
```

# Pydantic AI

From the creators of the amazing type safety / object-relational mapping library Pydantic comes Pydantic AI.  
   
My attempt at writing the tech writer in Pydantic AI clocked in at the slightly heavier 123-odd lines of code. 

The only reason this wasn't one of the lightest was its specific way to define tools:

* python methods require the @\<agent\_name\>.tool annotation  
* Optionally, it also requires a RunContext parameter to pass the directory of code being analysed.

Again, as for Langgraph, I don't understand python scoping rules enough to understand why this additional wrapper was required when other frameworks don't need it, but it translates to slightly higher friction and cognitive load as you have to understand what a RunContext is and why it's required. 

## Pydantic-AI Tech Writer Agent Code
```python
from pathlib import Path
import sys
from typing import Tuple
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

# Add noframework/python to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'noframework' / 'python'))

from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    TECH_WRITER_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args,
    MAX_ITERATIONS,
    vendor_model_with_colons,
)

from common.tools import find_all_matching_files, read_file
from common.logging import logger, configure_logging

class AnalysisContext(BaseModel):
    base_directory: str
    analysis_prompt: str

tech_writer = Agent(
    deps_type=AnalysisContext,
    result_type=str,
    system_prompt=TECH_WRITER_SYSTEM_PROMPT,
)

@tech_writer.tool
async def find_files(
    ctx: RunContext[AnalysisContext], 
    pattern: str = "*", 
    respect_gitignore: bool = True, 
    include_hidden: bool = False,
    include_subdirs: bool = True
) -> list[str]:
    return find_all_matching_files(
        directory=ctx.deps.base_directory,
        pattern=pattern,
        respect_gitignore=respect_gitignore,
        include_hidden=include_hidden,
        include_subdirs=include_subdirs,
        return_paths_as="str"
    )

@tech_writer.tool
async def read_file_content(ctx: RunContext[AnalysisContext], file_path: str) -> dict:
    if not Path(file_path).is_absolute():
        file_path = str(Path(ctx.deps.base_directory) / file_path)
    return read_file(file_path)

async def analyze_codebase(
    directory_path: str, 
    prompt_file_path: str, 
    model_name: str, 
    base_url: str = None, 
    repo_url: str = None,
    max_iterations: int = MAX_ITERATIONS # not used in this framework
) -> Tuple[str, str, str]:

    prompt = read_prompt_file(prompt_file_path)
    
    context = AnalysisContext(
        base_directory=directory_path,
        analysis_prompt=prompt
    )
    
    colon_delimited_vendor_model_pair = vendor_model_with_colons(model_name)
    
    result = await tech_writer.run(
        f"Base directory: {directory_path}\n\n{prompt}",
        deps=context,
        model=colon_delimited_vendor_model_pair
    )
    
    repo_name = Path(directory_path).name
    return result.output, repo_name, repo_url or ""


def main():
    import asyncio
    
    async def async_main():
        try:
            configure_logging()
            args = get_command_line_args()
            
            repo_url, directory_path = configure_code_base_source(
                args.repo, args.directory, args.cache_dir
            )
            
            analysis_result, repo_name, _ = await analyze_codebase(
                directory_path, 
                args.prompt_file, 
                args.model, 
                args.base_url, 
                repo_url,
                getattr(args, 'max_iters', MAX_ITERATIONS)
            )
            
            output_file = save_results(
                analysis_result, args.model, repo_name, 
                args.output_dir, args.extension, args.file_name
            )
            
            create_metadata(
                output_file, args.model, repo_url, repo_name, 
                analysis_result, getattr(args, 'eval_prompt', None)
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            sys.exit(1)
    
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
```

# Other Python Agent Maker Packages

In future I hope to cover the remaining 8 python package agent makers I've found so far:

* [Ag2](https://ag2.ai)  
* [AgentStack](https://github.com/AgentOps-AI/AgentStack)  
* [BeeAI](https://github.com/i-am-bee/beeai-framework) (IBM)  
* [Camel AI](https://github.com/camel-ai/camel)  
* [CrewAI](https://crewai.com)  
* [Griptape](https://github.com/griptape-ai/griptape)  
* [Semantic Kernel](https://github.com/microsoft/semantic-kernel) (Microsoft, multilingual)  
* [Smolagents](https://github.com/huggingface/smolagents) (HuggingFace)

# Python Agent Maker Servers

In addition, there are around 15 other open source python solutions, available only, as far as I could make out, as standalone servers. These I'll also assess at some point, but many cannot easily be scripted, they will be a lot more involved to assess:

* [Agent-S](https://github.com/simular-ai/Agent-S)  
* [AgentVerse](https://github.com/OpenBMB/AgentVerse)  
* [Archon](https://github.com/coleam00/Archon)  
* [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)  
* [deer-flow](https://github.com/bytedance/deer-flow) (ByteDance)  
* [dify](https://dify.ai)  
* [julep](https://julep.ai)  
* [Letta](https://github.com/cpacker/MemGPT)  
* [parlant](https://github.com/emcie-co/parlant)  
* [pippin](https://github.com/pippinlovesyou/pippin)  
* [potpie](https://github.com/potpie-ai/potpie)  
* [pyspur](https://github.com/PySpur-Dev/pyspur) (multilingual)  
* [rowboat](https://github.com/rowboatlabs/rowboat)  
* [suna](https://github.com/kortix-ai/suna)  
* [SuperAGI](https://github.com/TransformerOptimus/SuperAGI)  
* [Agent Zero](https://github.com/frdel/agent-zero)

# TypeScript Agent Makers

Outside Python the second largest set of open source agent makers are those made in TypeScript. 

* [BaseAI](https://github.com/LangbaseInc/BaseAI)  
* [Flowise](https://github.com/FlowiseAI/Flowise)  
* [Motia](https://github.com/MotiaDev/motia)  
* [N8n](https://github.com/n8n-io/n8n)  
* [Open-Cuak](https://github.com/Aident-AI/open-cuak)

# Other Languages

There are agent frameworks available in PHP, Ruby, Golang and Rust. I'll explore those in time. 