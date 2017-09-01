from setuptools import setup, find_packages

setup(
    name='holmes',
    version='0.1',
    description='',
    author='Shixiang Zhu',
    author_email='shixiang.zhu@gatech.edu',
    packages=find_packages(),
    install_requires=[
        'arrow',
        'requests',
        'amqp',
        'rabbitmq_hub'
    ],
    zip_safe=False)
