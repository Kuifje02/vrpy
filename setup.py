import setuptools

setuptools.setup(
    name="vrpy",
    version="0.4.0",
    description="A python framework for solving vehicle routing problems",
    license="MIT",
    author="Romain Montagne, David Torres",
    author_email="r.montagne@hotmail.fr",
    keywords=["vehicle routing problem", "vrp", "column generation"],
    long_description=open("README.rst", "r").read(),
    long_description_content_type="text/x-rst",
    url="https://github.com/Kuifje02/vrpy",
    packages=setuptools.find_packages(),
    install_requires=["cspy", "networkx", "numpy", "pulp"],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
