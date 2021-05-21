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

If running against DVWA, ensure that DVWA's security has been set to low, and the database has been setup.

Assuming the DVMA docker container is exposed on port 8080 you can run the crawler against it by running:

```
$ crawler http://localhost:8080/ --testing-dvwa
```
