from setuptools import setup, find_packages

with open('README.md') as readme_file:
    README = readme_file.read()

with open('HISTORY.md') as history_file:
    HISTORY = history_file.read()

setup_args = dict(
    name='rlockertools',
    version='0.1.5',
    description='Useful tools to interact with Resource Locker Project',
    long_description_content_type="text/markdown",
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    packages=find_packages(),
    author='Jim Erginbash',
    author_email='jimshapedcoding@gmail.com',
    keywords=['Rlocker', 'rlocker', 'ResourceLocker', 'Python 3', 'Resource Locker'],
    url='https://github.com/jimdevops19/rlockertools.git',
    download_url='https://pypi.org/project/rlockertools/'
)

install_requires = [
    'requests',
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)
