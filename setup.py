from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))


VERSION = '0.0.11'
DESCRIPTION = 'Scraping tradingview.com'
LONG_DESCRIPTION = 'A package that allows to retrieve data from tradingview.'

setup(
    name="tvw_scraper",
    version=VERSION,
    author="fip (Filipp Pozdniakov)",
    author_email="<ogremagi9@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    setup_requires=['wheel'],
    url = 'https://github.com/ogremagi4/tvw_scraper',
    install_requires = [],
    packages=find_packages(),
    keywords=['python', 'scraping', 'market data', 'tradingview'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)