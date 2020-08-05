import setuptools

with open('README.md', 'r', encoding='utf-8') as file:
  long_description = file.read()

install_requires = []
with open('requirements.txt') as file:
  install_requires = [line for line in file.read().splitlines() if len(line) > 0]

setuptools.setup(
  name='tdms2h5',
  version='1.0.0',
  author='BlueQuartz Software, LLC',
  author_email='info@bluequartz.net',
  description='tdms2h5 is a Python package for converting TDMS files into HDF5 files',
  long_description=long_description,
  long_description_content_type='text/markdown',
  url='https://github.com/bluequartzsoftware/TDMS_Data_CDME',
  py_modules=['tdms2h5'],
  entry_points={'console_scripts' : ['tdms2h5=tdms2h5:main']},
  license='BSD',
  platforms='any',
  classifiers=[
      'Programming Language :: Python :: 3',
      'License :: OSI Approved :: BSD License'
  ],
  python_requires='>=3',
  install_requires=install_requires
)
