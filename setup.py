from distutils.core import setup
from Cython.Build import cythonize
import os
# setup(ext_modules = cythonize(["Base_check.py", "Card_check.py", "Query_answer_check.py", "Same_frame_check.py", "Language_matching.py", "Speak_extract.py"]))
# setup(ext_modules = cythonize(["Operation_check.py"]))
# python setup.py build_ext --inplace


# 获取所有.py文件（排除特定文件）
def get_py_files():
    py_files = []
    for root, dirs, files in os.walk('.'):
        # 排除特定目录
        if 'BW' in dirs:
            dirs.remove('BW')
            
        # 排除特定文件
        excluded_files = ['main.py', 'setup.py', '__init__.py']  # 保留__init__.py
        for file in excluded_files:
            if file in files:
                files.remove(file)
        
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files

setup(
    ext_modules = cythonize(get_py_files(), compiler_directives={'language_level': "3"})
)

# print(get_py_files())