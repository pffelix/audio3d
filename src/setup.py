# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
setup(
    name = "audio3d",
    version = "1.0",
    packages = find_packages(),
    include_package_data = True,
    package_data = {
        'audio3d': ['*.png','*.wav'],
    },
    install_requires = ['pyopengl','pyaudio','pyside'],
    entry_points={
        'console_scripts': [
            'audio3d = audio3d.__main__:main',
        ],
    }

)
