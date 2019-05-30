from distutils.core import setup
import setuptools

setup(name='pywise',
      version='0.1.0',
      author="Na'ama Hallakoun",
      author_email='naama@wise.tau.ac.il',
      description='Image reduction pipeline for the Wise Observatory',
      long_description=open('README.md').read(),
      url='https://github.com/naamach/pywise',
      license='LICENSE.txt',
      packages=setuptools.find_packages(),
      install_requires=['astropy', 'configparser', 'ccdproc', 'numpy'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering :: Astronomy'],
      scripts=['bin/wise_reduce']
      )
