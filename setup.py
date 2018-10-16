from setuptools import setup


if __name__ == "__main__":
    setup(
        name='asyncio_debug_patch',
        description='Patch to enrich asyncio debugging information',
        license='MIT license',
        python_requires='>=3.6',
        py_modules=['asyncio_debug_patch'],
    )
