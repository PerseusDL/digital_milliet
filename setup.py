from setuptools import setup

setup(
    name='digital_milliet',
    packages=['digital_milliet'],
    include_package_data=True,
    test_suite="tests",
    install_requires=[
        'flask==1.0',
        "Flask-OAuthlib>=0.9.3",
        "Flask-Babel==0.9",
        "Flask-Bower==1.0.1",
        "requests>=2.8.1",
        "Flask-Cache==0.13.1",
        "requests-cache==0.4.9",
        "flask-cors==2.0.0",
        "Flask-PyMongo==0.3.1",
        "Flask-Markdown",
        "MyCapytain==2.0.0b8",
        "PyYaml",
        "setuptools==36.5.0",
        "Flask-Env==1.0.1"
    ],
    setup_requires=[
    ],
    tests_require=[
    ]
)
