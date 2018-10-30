from distutils.core import setup

if __name__ == '__main__':
    setup(
        name='FontSquirrel',
        description='Font Squirrel CLI',
        long_description=open('README.md').read(),
        version='1.0.1',
        author='Kevin Selwyn',
        author_email='kevinselwyn@gmail.com',
        url='https://github.com/kevinselwyn/fontsquirrel',
        packages=['fontsquirrel'],
        license='GPLv3',
        install_requires=[
            'requests==2.20.0',
            'progressbar==2.3'
        ],
        scripts=['bin/fontsquirrel']
    )
