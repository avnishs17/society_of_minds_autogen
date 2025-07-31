from setuptools import setup, find_packages

__version__ = "0.0.0"

REPO_NAME = "som_with_human_in_loop"
AUTHOR_USER_NAME = "avnishs17"
SRC_REPO = "som_with_human_in_loop"
AUTHOR_EMAIL = "avnish1708@gmail.com"


setup(
    name=SRC_REPO,
    version=__version__,
    author=AUTHOR_USER_NAME,
    author_email=AUTHOR_EMAIL,
    description="Society of mind with human in loop",
    packages=find_packages(),
)