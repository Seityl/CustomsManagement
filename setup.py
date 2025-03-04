from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

from customs_management import __version__ as version

setup(
	name = 'customs_management',
	version = version,
	description = 'Facilitates invoice verification, custom entry creation, and item pricing.',
	author = 'Jollys Pharmacy Limiteed',
	author_email = 'cdgrant@jollysonline.com',
	packages = find_packages(),
	zip_safe = False,
	include_package_data = True,
	install_requires = install_requires
)
