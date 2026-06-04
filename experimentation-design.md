# Design

## Problem
We want to analyize the response patterns of LLMs to a given prompt. E.g. what types of things does an LLM recommend?

## Design

Query builder:
- takes a template (yaml) and constructs it into a query. The template is a yaml, its name is the prefix
- records: {constructed-query-id:str}, {query:str}, {metadata}
- will eventually go into a db, for now this will go into queries/<tempalate-prefix>/<id>/query.md

Query enqueuer:
- Queues a query (outputted from the builder) for the executor. Filters which queries we want to execute and which models we send it to.
- Will eventually go to sqs, for now send each to a new queued_queries/<id>/query.yaml
- each query will contain information about:
    - target model
    - constructed query id
    -

Query Executor:
- Takes a template and sends it to a
