from setuptools import setup, find_packages

setup(
    name="mcp-tutorial-server",
    version="1.0.0",
    description="A comprehensive, hands-on tutorial for learning MCP (Model Context Protocol) server development with working examples and debugging tools",
    author="Dustin",
    author_email="6962246+djdarcy@users.noreply.github.com",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Education",
        "Topic :: Documentation",
    ],
    python_requires=">=3.10",
    keywords="mcp, model-context-protocol, tutorial, server, development, claude",
    url="https://github.com/djdarcy/MCP-Server-Tutorial",
)
