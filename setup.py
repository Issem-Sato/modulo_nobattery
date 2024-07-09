from setuptools import setup, find_packages

setup(
    name='modulo_nobattery',  
    version='0.1', 
    packages=find_packages(),
    install_requires=[],
    author='Agenzia APE',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Issem-Sato/modulo_nobattery',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
