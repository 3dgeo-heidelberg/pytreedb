# Contributing

Thanks for considering contributing! Please read this document to learn the various ways you can contribute to this project and how to go about doing it.
> The instructions in this file are based on [this template](https://github.com/allenai/python-package-template/blob/main/CONTRIBUTING.md).

## Bug reports and feature requests

### Did you find a bug?

First, do [a quick search](https://github.com/3dgeo-heidelberg/pytreedb/issues) to see whether your issue has already been reported.
If your issue has already been reported, please comment on the existing issue.

Otherwise, open [a new GitHub issue](https://github.com/3dgeo-heidelberg/pytreedb/issues/new).  Be sure to include a clear title
and description.  The description should include as much relevant information as possible.  The description should
explain how to reproduce the erroneous behavior as well as the behavior you expect to see.  Ideally you would include a
code sample or an executable test case demonstrating the expected behavior.

### Do you have a suggestion for an enhancement or new feature?

We use GitHub issues to track feature requests. Before you create a feature request:

* Make sure you have a clear idea of the enhancement you would like. If you have a vague idea, consider discussing
it first on a GitHub issue.
* Check the documentation to make sure your feature does not already exist.
* Do [a quick search](https://github.com/3dgeo-heidelberg/pytreedb/issues) to see whether your feature has already been suggested.

When creating your request, please:

* Provide a clear title and description.
* Explain why the enhancement would be useful. It may be helpful to highlight the feature in other libraries.
* Include code examples to demonstrate how the enhancement would be used.

## Making a pull request

When you're ready to contribute code to address an open issue, please follow these guidelines to help us be able to review your pull request (PR) quickly.

1. **Fork the repository** (only do this once)

    <details><summary>Expand details 👇</summary><br/>

    If you haven't already done so, please [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) this repository on GitHub.

    </details>
   
2. **Clone the repository and set up your environment** (only do this once)

    <details><summary>Expand details 👇</summary><br/>

    If you only make small changes, like fixing a typo, you can skip cloning and edit files online. 

    For bigger changes in the source code, clone your fork locally with

        git clone https://github.com/USERNAME/pytreedb.git

    or 

        git clone git@github.com:USERNAME/pytreedb.git

    Finally, you'll need to create a Python 3 environment suitable for working on this project. There a number of tools out there that making working with virtual environments easier.
    We recommend [Anaconda](https://anaconda.org/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

    Once you installed Anaconda or Miniconda, open an Anaconda/Miniconda prompt and navigate to your `pytreedb` directory. 

    Then you can create and activate a new Python environment from our [environment.yml](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/environment.yml) by running:

        conda env create --file environment.yml --force
        conda activate pytreedb
   
    Our continuous integration (CI) testing runs [a number of checks](https://github.com/3dgeo-heidelberg/pytreedb/actions) for each pull request on [GitHub Actions](https://github.com/features/actions). 
    You can run the linters and the tests locally, which is something you should do *before* opening a PR to help speed up the review process and make it easier for us.
    For this, pre-commit hooks are very useful. These are scripts that run before your git commit is accepted and which ensure that you commit well-formatted code.
    
    The `pre-commit` package is included in our [`environment.yml`](environment.yml) and [`requirements.txt`](requirements.txt), so at this point, you probably have it installed.
    To install the pre-commit hooks that we defined for our repository (see [.pre-commit-config.yaml](.pre-commit-config.yaml)), please run
 
        pre-commit install
    
    Now, the code you push is checked for syntax errors before you are able to commit.
    If you try to commit your changes and are absolutely not able to fix all of these syntax errors, you can (as an exception) run

        git commit -m "your useful commit message" --no-verify

    to bypass the pre-commit hooks.

    </details>

3. **Edit locally or edit online**

   <details><summary>Expand details 👇</summary><br/>
   
   Work on your fix or enhancement by editing files locally or online and committing your changes.
   
   </details>

4. **Test your changes**

    <details><summary>Expand details 👇</summary><br/>

    We strive to maintain high test coverage, so substantial contributions to [`pytreedb/db.py`](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/pytreedb/db.py) or [`pytreedb/db_utils.py`](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/pytreedb/db_utils.py) should include additions to [the unit tests](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/pytreedb/test). 
    These tests are run with [`pytest`](https://docs.pytest.org/en/latest/), which you can use to locally run any test modules that you've added or changed.
    
        python -m pytest pytreedb

    We use pytest markers to categorize our tests into `imports`, `export` and `query` (see [pyproject.toml](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/pyproject.toml)). 
    This allows you to test features of a specific category, e.g.:

      python -m pytest pytreedb -m query

    If your contribution involves additions to any public part of the API, we require that you write docstrings
    for each function, method, class, or module that you add.
    See the [Writing docstrings](#writing-docstrings) section below for details on the syntax.
    You should test to make sure the API documentation can build without errors by running

        cd doc  
        make html

    If the build fails, it's most likely due to small formatting issues. If the error message isn't clear, feel free to comment on this in your pull request.

    </details>

5. **Create a Pull Request (PR) using the GitHub web interface**

   <details><summary>Expand details 👇</summary><br/>
   
   On your fork in GitHub, navigate to the `Pull requests` tab and click `New pull request`.
   As base repository, choose `3dgeo-heidelberg/pytreedb`, as head repository, keep your own fork. You may further select the branch you want to pull, if you created one for your feature.
   
   Click `Create pull request` and make sure you add a clear description of the problem and the solution. If applicable, include a link to relevant issues.

   Make sure your PR is up to date using the PR interface.
   If you see the warning `This branch is out-of-date with the base branch`, select `Update branch`. If the branch has conflicts that must be resolved, use the web editor or the command line to `Resolve conflicts`.

   We look forward to reviewing your PR!

   </details>

### Writing docstrings

We use [Sphinx](https://www.sphinx-doc.org/en/master/index.html) to build our API docs, which automatically parses all docstrings
of public classes and methods using the [autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) extension.
Please refer to the documentation of the [Sphinx/ReStructuredText docstring format](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html) to learn about the syntax.
