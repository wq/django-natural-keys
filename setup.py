from setuptools import setup

LONG_DESCRIPTION = """
Enhanced support for natural keys in Django and Django REST Framework
"""


def readme():
    try:
        readme = open('README.md')
    except IOError:
        return LONG_DESCRIPTION
    else:
        return readme.read()


setup(
    name='natural-keys',
    use_scm_version=True,
    author='S. Andrew Sheppard',
    author_email='andrew@wq.io',
    url='https://github.com/wq/django-natural-keys',
    license='MIT',
    packages=['natural_keys'],
    description=LONG_DESCRIPTION.strip(),
    long_description=readme(),
    long_description_content_type="text/markdown",
    install_requires=[
        'html-json-forms>=1.0.0',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Topic :: Database',
    ],
    setup_requires=[
        'setuptools_scm',
    ],
)
