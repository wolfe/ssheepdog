from setuptools import setup

f = open('README.md')
readme = f.read()
f.close()

setup(
    name='ssheepdog',
    version='1.0',
    description=('ssheepdog is an app to manage ssh authorized_keys'
                 ' files using scp.'),
    long_description=readme,
    author='David Wolfe',
    author_email='davidgameswolfe@gmail.com',
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
