from setuptools import setup

setup(
    name='GetTopNIds',
    version='1.0',
    py_modules=['n_largest', 'param_types', 'util', 'constants'],
    install_requires=[
        'click',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        nlargest=n_largest:n_largest_cli
    ''',
    python_requires='>=3.8',
)