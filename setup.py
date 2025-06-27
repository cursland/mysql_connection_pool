from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mysql-connection-pool",
    version="1.1.1",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",    install_requires=[
        "mysql-connector-python>=8.4.0",
        "sqlglot>=25.0.0",
    ],
    keywords="mysql database connection pool threading",
)