from setuptools import setup

setup(
    name='GetTopNIds',
    version='1.0',
    py_modules=['get_top_n_ids', 'n_largest_cache', 'constants'],
    install_requires=[
        'click',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        get-n-largest=get_top_n_ids:get_n_largest
        n-largest-clear-cache=n_largest_cache:clear_cache
        n-largest-set-cache=n_largest_cache:set_cache_dir
    ''',
    python_requires='>=3.8',
)