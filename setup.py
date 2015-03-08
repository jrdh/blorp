from distutils.core import setup

setup(
    name='Blorp',
    version='0.2.0',
    author='Josh Humphries',
    author_email='jrdhumphries@gmail.com',
    packages=['blorp'],
    scripts=[],
    # url='http://pypi.python.org/pypi/Blorp/',
    license='LICENSE.txt',
    description='Socket.io to python bridge using redis and asyncio',
    long_description=open('README.md').read(),
    install_requires=[
        'anyjson == 0.3.3',
        'asyncio-redis == 0.13.4',
        'redis == 2.10.3',
    ],
)