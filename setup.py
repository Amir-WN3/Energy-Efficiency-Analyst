from setuptools import setup, find_packages # type: ignore
from typing import List

def get_requirements(file_path: str) -> List[str]:
    '''
    This function returns the list of requirements
    '''
    requirements = []
    HYPHEN_E_DOT = '-e .'

    with open(file_path, 'r') as file:
        requirements = file.readlines()
        requirements = [req.replace('\n','') for req in requirements]

        if HYPHEN_E_DOT in requirements:
            requirements.remove(HYPHEN_E_DOT)

    return requirements

setup(
    name = 'energy-efficiency-analyst',
    version = '0.0.1',
    packages = find_packages(),
    install_requires = get_requirements('requirements.txt'),
)