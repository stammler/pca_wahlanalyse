from setuptools import find_packages
from setuptools import setup

package_name = "pca_wahl"

setup(
    name=package_name,

    description="Hauptkomponentenanalyse zur Wahlen",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    version="0.1.0",
    license="BSD",
    packages=find_packages(),
    install_requires=[
        "matplotlib",
        "numpy",
        "pandas",
        "scikit-learn"
    ],
    include_package_data=True,
    zip_safe=False,
)