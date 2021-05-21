# Crawler-TT
Crawler tech test for AppCheck

## Running Instructions

This project uses Poetry for dependency management and requires Python >= 3.8 to run.

With Python and Poetry installed from the root project directory you can install the project, and it's dependencies
with:

```
$ poetry install --no-dev
```

This installs the crawler binary which can then be called from the command line:

```
$ crawler -h
```

This will describe what CLI arguments can be passed to the crawler to run in standalone mode.

If running against DVWA, ensure that the database has been set up and remember to include the `testing-dvwa` cli flag.

Assuming the DVMA docker container is exposed on port 8080 you can run the crawler against it by running:

```
$ crawler http://localhost:8080/ --testing-dvwa
```

## Architecture

For scalability a SaaS type system should be designed which would allow for the effective management of SQLI crawlers.

The architecture would consist of a frontend that would allow management/running of crawlers as well as allowing for
the addition of new SQLI payloads. The backend would provide an API to allow communication with the frontend and other
external systems.

Workers will perform the actual crawling/testing and can be scaled to meet demand. All results from these crawls will
be stored to an SQL type database for retrieval by the backend

![Architecture Diagram](https://github.com/DurzoB5/Crawler-TT/blob/main/images/Architecture.png)

## Crawler

The crawler itself has the capability to be run in "service" mode with the use of Celery as part of a SaaS type system
or as a standalone program which can be run on its own. As the crawler crawls it stores the result of any URL processed
to a ProgressHandler class which handles storing the result to different places, for example in standalone mode the
StandaloneProgressHandler is used which stores each URL tested to a JSON file, if the crawler dies/fails part way
through a crawl providing the same json file again to the CLI will cause it to continue from where it left off, if
running in service mode the ServiceProgressHandler would be used which could store each url processed to a database.

## Testing

As the crawler can be run standalone this would allow for easier methods of testing the crawler against known
vulnerable web apps. This can include testing of the code itself (having known results from something like DVWA) as well
as testing of new payloads. When running on a SaaS type system a DVMA (or other vulnerable) docker image could be spun
up on a segregated network that would allow for testing of new payloads through the frontend.

## Future Considerations

Given more time I would of liked to include functional tests into the code. The celery shared task decorator should be
given an overridden base argument to handle random failures within the task. Additional functionality would need to be
added to allow a more dynamic capability for logging into web apps. The ProgressHandler classes can be extended to
support more storage solutions without the need for major code changes.
