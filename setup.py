import os
import sys

import setuptools

ROOT = os.path.dirname(__file__)

if sys.version_info < (3, 6, 0):
    sys.exit("Python 3.6.0 is the minimum required version for building this package")

with open(os.path.join(ROOT, "README.md")) as f:
    long_description = f.read()

setuptools.setup(
    name="assisted-events-scrape",
    setup_requires=["vcversioner"],
    vcversioner={"vcs_args": ["git", "describe", "--tags", "--long"]},
    description="Export your test suites and cases to JUnit report using decorators",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openshift-assisted/assisted-events-scrape",
    author="RedHat",
    author_email="UNKNOWN",
    license="Apache License 2.0",
    packages=setuptools.find_packages("assisted-events-scrape"),
    package_dir={"": "assisted-events-scrape"},
    install_requires=["urllib3>=1.26.7",
                      "elasticsearch<8.9.0",
                      "requests>=2.26.0",
                      "kubernetes>=18.20.0",
                      "retry>=0.9.2",
                      "waiting>=1.4.1",
                      "assisted-service-client>=1.0.27.1"],
    entry_points={
        'console_scripts': [
            'events_scrape = events_scrape.events_scrape:main',
            'ccx_export = ccx_export:export_events',
            'ccx_export_cleanup = ccx_export:delete_s3_objects',
        ],
    },
    include_package_data=True,
    python_requires=">=3.6.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        'License :: OSI Approved :: Apache Software License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Testing",
    ],
)
