from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = [l.strip() for l in f if l.strip() and not l.startswith("#")]

setup(
    name="inovaya_gdp",
    version="1.0.0",
    description="Configuration native-first ERP Gestion de Projets pour InovaYa",
    author="InovaYa",
    author_email="info@inovaya.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
