from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="softia_core",
    version="1.0.0",
    description="Socle technique Frappe/ERPNext réutilisable — base pour les apps prospects Softia",
    author="Softia",
    author_email="dev@softia.fr",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
