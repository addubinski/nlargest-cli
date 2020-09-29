from setuptools import setup

setup(
    name='GetTopNIds',
    version='1.0',
    py_modules=['get_top_n_ids'],
    install_requires=[
        'click',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        get-n-largest=get_top_n_ids:get_n_largest
    ''',
    python_requires='>=3.8',
)