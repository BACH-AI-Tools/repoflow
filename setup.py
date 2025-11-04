"""RepoFlow 安装配置"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="repoflow",
    version="1.0.0",
    author="BACH-AI-Tools",
    author_email="",
    description="自动化项目发布工具 - 简化从本地到GitHub的完整流程",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BACH-AI-Tools/RepoFlow",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "PyGithub>=2.1.1",
        "GitPython>=3.1.40",
        "python-dotenv>=1.0.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "pyyaml>=6.0.1",
    ],
    entry_points={
        'console_scripts': [
            'repoflow=repoflow:cli',
        ],
    },
    include_package_data=True,
    keywords='automation github cicd docker npm pypi deployment',
    project_urls={
        'Bug Reports': 'https://github.com/BACH-AI-Tools/RepoFlow/issues',
        'Source': 'https://github.com/BACH-AI-Tools/RepoFlow',
    },
)

