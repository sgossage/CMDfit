from setuptools import setup

setup(name='cmdfit',
      version='0.1',
      description='Tool for fitting isochrones to CMD data.',
      url='https://github.com/p201-sp2016/CMDfit',
      author='Seth Gossage',
      author_email='Sethg45@gmail.com',
      license='IDK',
      packages=['cmdfit'],
      install_requires=[
          'numpy',
          'corner'
      ],
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose'],
)
