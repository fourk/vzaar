from distutils.core import setup

with open('README.md') as file:
    long_description = file.read()

setup(name='vzaar',
        description="Python library wrapping Vzaar's v1.0 API",
        long_description=long_description,
        keywords=['vzaar', 'video'],
        author="James Burkhart",
        author_email="pyvzaar@jamesburkhart.com",
        url="https://github.com/fourk/vzaar",
        version='1.0.7',
        py_modules=['vzaar'])
