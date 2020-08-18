from setuptools import setup, find_packages


setup(
    name="dusk",
    version="0.5.0",
    packages=find_packages(),
    author="MeteoSwiss",
    author_email="Benjamin.Weber@MeteoSwiss.ch",
    description="An eDSL front-end for Numerical Weather Prediction dynamical cores",
    keywords="dawn SIR eDSL DSL NWP dycore ICON",
    url="https://github.com/dawn-ico/dusk",
    license="MIT License",
    python_requires=">=3.8",
    install_requires=["dawn4py>=0.0.2"],
    entry_points={"console_scripts": ["dusk = dusk.cli:main"]},
)
