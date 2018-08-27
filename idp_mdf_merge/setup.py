from setuptools import setup
import py2exe


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='idp_mdf_merge',
      version='1.1.0',
      description='Merges IDP Message Definition Files',
      # url='https://github.com/gbrucepayne/idp_mdf_merge',
      author='Geoff Bruce-Payne',
      author_email='geoff.bruce-payne@inmarsat.com',
      license='MIT',
      packages=['idp_mdf_merge'],
      install_requires=[
          'xml.etree.ElementTree',
          'Tkinter',
          'tkFileDialog',
          'ntpath',
          'httplib',
          'argparse',
          'sys',
          'os'
      ],
      include_package_data=True,
      zip_safe=False)
