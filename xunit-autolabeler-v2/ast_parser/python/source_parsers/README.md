# Source Parsers - Python

## What are these for?
Given an abstract syntax tree (AST) representing a snippet-containing Python file, these libraries extract references to the snippet methods from that AST.

They then convert those references into snippet-type-agnostic data that can be processed by a Python-specific parser (like that in `ast_parser/python`).

## What formats are supported?
Currently, the following snippet formats are supported:
1. _Directly-invoked snippets:_ snippets triggered by Python methods directly called within a test
1. _Flask HTTP routes:_ snippets triggered by Flask HTTP routes
1. _webapp2 HTTP routes:_ snippets triggered by webapp2 HTTP routes

## Usage
These files are intended to be libraries, and should not be invoked directly.
