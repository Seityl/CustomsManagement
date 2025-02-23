from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in customs_management/__init__.py
from customs_management import __version__ as version

setup(
	name="customs_management",
	version=version,
	description="Customs Management",
	author="Sudeep Kulkarni",
	author_email="asoral@dexiss.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
