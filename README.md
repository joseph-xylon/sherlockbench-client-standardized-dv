# SherlockBench Clients

This codebase contains the clients for the SherlockBench AI benchmarking system.

There is a Python package for each LLM provider, sharing as much code as is
reasonable but allowing to accommodate the idiosyncrasies for each provider.

Essentially the clients are sitting in-between two APIs. The LLM provider's API
and the SherlockBench API.

If you wonder why we didn't "just use LangChain" - in my experience LangChain
does not have stable support for tool calling and structured outputs accross
different providers, and isn't maintained as pro-actively as I'd like.

## Main Website
The project homepage: https://sherlockbench.com

## Running

If you want to run this benchmark yourself, you will need:
- An account and API key for whichever LLM provider you want to use
- A computer to install Python and PostgreSQL on. Postgres is how it stores analytics for each run

General instructions follow. Alternatively you may watch this video for Ubuntu instructions: [Installing SherlockBench Client](https://youtu.be/qNIXQTtuFYs).

Checkout this code.

Install these:
- PostgreSQL
  - server
  - client
  - libpq-dev
- Python3:
  - runtime
  - pip
  - virtualenv

Create a postgresql database and user.

Create a couple of config files:

A `resources/config.yaml` should look like this (uncomment sections as appropriate):
```
---

# the base URL of the SherlockBench API
base-url: "http://0.0.0.0:3000/api/"
#base-url: "https://api.sherlockbench.com/api/"
msg-limit: 50

providers:
  openai:
    model: "gpt-4o-mini-2024-07-18"
    #model: "gpt-4o-2024-08-06"
    #model: "o3-mini-2025-01-31"
    rate-limit: 5

  anthropic:
    model: "claude-3-5-haiku-20241022"
    #model: "claude-3-5-sonnet-20241022"
    rate-limit: 10

  google:
    model: "gemini-2.0-flash"
    #model: "gemini-2.0-pro-exp-02-05"
    rate-limit: 10

  fireworks:
    model: "accounts/fireworks/models/llama-v3p1-405b-instruct"
    rate-limit: 10

```

And a `resources/credentials.yaml` containing your db credentials and API keys:
```
---

postgres-url: "postgresql://user:password@localhost/dbname"
api-keys:
  anthropic: ""
  openai: ""
  google: ""
  fireworks: ""
```

Running it should be essentially:
- make a virtualenv and activate it
- install sherlockbench into your virtualenv with `pip install -e .`
- run `alembic upgrade head` to create the database tables
- type the name of the provider entry-point to run the benchmark (see setup.cfg)

## Database Analysis
There are two tables in the database;
- runs stores general information about the test run and it's results
- attempts stores the logs for the individual attempts and some metadata

### Example queries
If you know SQL you can do some analysis of the results.
