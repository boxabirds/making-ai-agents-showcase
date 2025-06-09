#!/bin/bash

# BabyAGI Python Package Installation and Usage Script

# Install BabyAGI package using uv pip
uv venv -p 3.11

uv pip install babyagi

# Client and Server usage instructions

# Client usage (import and use functions in Python)
# Example usage:
# import babyagi
# @babyagi.register_function()
# def world():
#     return "world"
#
# @babyagi.register_function(dependencies=["world"])
# def hello_world():
#     x = world()
#     return f"Hello {x}!"
#
# print(babyagi.hello_world())  # Output: Hello world!

# Server usage (run the dashboard)
# Run this Python code to start the dashboard server:
# import babyagi
# if __name__ == "__main__":
#     app = babyagi.create_app('/dashboard')
#     app.run(host='0.0.0.0', port=8080)
#
# Then open your browser at http://localhost:8080/dashboard to access the dashboard.