from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mysql-connection-pool",
    version="1.0.2",
    author="Cursland",
    author_email="",
    description="Una clase para manejar conexiones a MySQL con un pool de conexiones y soporte para múltiples hilos.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cursland/mysql_connection_pool",
    project_urls={
        "Author": "https://cursland.com",
        "GitHub": "https://github.com/cursland/mysql_connection_pool"
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "mysql-connector-python>=8.0.0",
        "sqlparse>=0.4.0",
    ],
    keywords="mysql database connection pool threading",
)