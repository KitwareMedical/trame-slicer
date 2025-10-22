# Contributing to trame-slicer

1. Clone the repository using `git clone`
1. Install the dev dependencies via `pip install pre-commit`
1. Run `pre-commit install` to set up pre-commit hooks
1. Make changes to the code, and commit your changes to a separate branch
1. Create a fork of the repository on GitHub
1. Push your branch to your fork, and open a pull request

## Testing

The library testing rely on the trame-slicer test data. To setup your testing
environment :

1. Download the [trame-slicer-test-data]{.title-ref} zip file available in this
   repository\'s release page
1. Unzip the file content to the [tests/data]{.title-ref} folder
1. Install the test requirements using pip using the `pip install .[dev]`
   command
1. Install playwright browsers using the `playwright install` command
1. [Linux] Install playwright dependencies using the `playwright install-deps`
   command
1. Run the tests using the pytest module `python -m pytest tests`

## Interactivity

Some tests allow for interactive interaction with the views and can be activated
by using the following arguments :

`python -m pytest tests --render-interactive=<interaction_time_limit_s>`

The interactivity time limit will apply to tests using a trame server in an
asyncio tasks. Interactivity for VTK render window logic will require manually
closing the windows to stop the interaction.

## Commit messages

trame-slicer follows trame\'s commit message convention to be compatible with
it\'s CI features including the auto semantic release.

## Tips

1. When first creating a new project, it is helpful to run
   `pre-commit run --all-files` to ensure all files pass the pre-commit checks.
1. A quick way to fix `black` issues is by installing black
   (`pip install black`) and running the `black` command at the root of your
   repository.
1. Sometimes, `black` and `flake8` do not agree. Add options to your `.flake8`
   file to fix these things. See the
   [flake8 configuration docs](https://flake8.pycqa.org/en/latest/user/configuration.html)
   for more details.
1. A quick way to fix `codespell` issues is by installing codespell
   (`pip install codespell`) and running the `codespell -w` command at the root
   of your directory.
1. The
   [.codespellrc file](https://github.com/codespell-project/codespell#using-a-config-file)
   can be used fix any other codespell issues, such as ignoring certain files,
   directories, words, or regular expressions.
