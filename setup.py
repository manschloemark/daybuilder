# TODO : Decide on a license and learn how to use this properly
import setuptools

with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(
        name = "daybuilder-manschloemark",
        version = "0.0.1", # Idk version conventions
        author = "Mark Schloeman",
        author_email = "mschloeman1@my.brookdalecc.edu",
        description = "Digital Daily Planner",
        long_description = long_description,
        long_description_content_type = "text/markdown",
        url = "https://github.com/manschloemark/daybuilder",
        packages = setuptools.find_packages(),
        classifiers = [
            "Programming Language :: Python :: 3",
            "License :: ",
            "Operating System :: OS Independent",
            ],
        python_requires = ">=3.6"
)
