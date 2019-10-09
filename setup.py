from setuptools import find_packages, setup


def requirements(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
    return lines

setup(
    name="contrail-vcenter-manager",
    version="0.1dev",
    packages=find_packages(),
    package_data={'': ['*.html', '*.css', '*.xml', '*.yml']},
    zip_safe=False,
    long_description="Contrail vCenter Manager",
    install_requires=requirements('requirements.txt'),
    entry_points = {
        'console_scripts' : [
            'contrail-vcenter-manager = cvm:server_main',
        ],
    },

)
