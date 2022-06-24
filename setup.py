from setuptools import setup, find_packages

setup(
  name = 'wiki-score',
  packages = find_packages(exclude=[]),
  include_package_data = True,
  entry_points={
    'console_scripts': [
    # todo: add here
    ],
  },
  version = '0.0.88',
  license='?',
  description = '?',
  author = '',
  author_email = '',
  url = 'https://github.com/Augustoni/wiki-score/',
  keywords = [
    'wikipedia','science','history of science'
  ],
  install_requires=[
"wikipedia", "setuptools", "pywikibot", "mwparserfromhell", "pandas", "numpy", "scipy" ,"nltk", "tqdm", "seaborn", "pyqt5", "pyqtwebengine", "ruamel-yaml", "lxml", "logging"
  ])