from setuptools import setup, find_packages
import cachemodel

setup(
    name='django-cachemodel',
    version=".".join(map(str, cachemodel.VERSION)),
    packages = find_packages(),

    author = 'Concentric Sky',
    author_email = 'django@concentricsky.com',
    description = 'Concentric Sky\'s cachemodel library',
    license = 'Apache2'
)
