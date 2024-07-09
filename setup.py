from setuptools import setup, find_packages

setup(
    name='modulo_nobattery',  # Nome del pacchetto
    version='0.1',  # Versione del pacchetto
    packages=find_packages(),
    install_requires=[],  # Elenca qui le dipendenze del tuo pacchetto, se ce ne sono
    author='Il tuo nome',
    author_email='tuo.email@example.com',
    description='Una breve descrizione del pacchetto',
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
