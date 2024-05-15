# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Quahl'
copyright = '2024, Florian Breit'
author = 'Florian Breit'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
]

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'inherited-members': False,
    'show-inheritance': True,
    'ignore-module-all': False,
    'exclude-members': 'staticMetaObject, __new__',
}

autodoc_class_signature = 'separated'
autodoc_member_order = 'groupwise'
autodoc_typehints = 'both'
autodoc_preserve_defaults = True
autodoc_show_sourcelink = True
python_use_unqualified_type_names = True

default_role = 'py:obj'
add_module_names = False
modindex_common_prefix = ['quahl']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
