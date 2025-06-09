#!/bin/bash

# Installation instructions for Water - multi-agent orchestration framework

# Install the package using pip (Python package manager)
uv venv -p 3.13
uv pip install water-ai

# Basic usage instructions (Python)
# To run the example usage, create a Python script with the following content:
# 
# import asyncio
# from water import Flow, create_task
# from pydantic import BaseModel
#
# class NumberInput(BaseModel):
#     value: int
#
# class NumberOutput(BaseModel):
#     result: int
#
# def add_five(params, context):
#     return {"result": params["input_data"]["value"] + 5}
#
# math_task = create_task(
#     id="math_task",
#     description="Math task",
#     input_schema=NumberInput,
#     output_schema=NumberOutput,
#     execute=add_five
# )
#
# flow = Flow(id="my_flow", description="My flow").then(math_task).register()
#
# async def main():
#     result = await flow.run({"value": 10})
#     print(result)
#
# if __name__ == "__main__":
#     asyncio.run(main())

# No client/server instructions found in the README; this is a Python package to be used as a library.