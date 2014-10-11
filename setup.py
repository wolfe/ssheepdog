from setuptools import setup, find_packages

f = open('README.md')
readme = f.read()
f.close()

setup(
    name='ssheepdog',
    version='1.1',
    description=('ssheepdog is an app to manage ssh authorized_keys'
                 ' files using scp.'),
    long_description=readme,
    author='David Wolfe',
    author_email='davidgameswolfe@gmail.com',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    url='https://github.com/wolfe/ssheepdog/',
    license='BSD',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
