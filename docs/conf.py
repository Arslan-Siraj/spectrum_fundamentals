#!/usr/bin/env python
# mypy: ignore-errors
# spectrum_fundamentals documentation build configuration file
#
# If extensions (or modules to document with autodoc) are in another
# directory, add these directories to sys.path here. If the directory is
# relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
#
import inspect
import os
import sys
from datetime import datetime
from pathlib import Path

from jinja2.defaults import DEFAULT_FILTERS

sys.path.insert(0, os.path.abspath(".."))


# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.

# Add 'sphinx_automodapi.automodapi' if you want to build modules
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    "sphinx_click",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "Spectrum-IO"
author = "Oktoberfest development team"
copyright = f"{datetime.now():%Y}, Wilhelmlab at Technical University of Munich"

# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The short X.Y version.
version = "0.7.4"
# The full version, including alpha/beta/rc tags.
release = "0.7.4"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

suppress_warnings = [
    "ref.citation",
]

# -- Options for HTML output -------------------------------------------

html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": "wilhelm-lab",  # Username
    "github_repo": "spectrum_fundamentals",  # Repo name
    "github_version": "development",  # Version
    "conf_py_path": "/docs/",  # Path in the checkout to the docs root
    "github_url": "https://github.com/wilhelm-lab/spectrum_fundamentals/",
}

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a
# theme further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = dict(
    navigation_depth=4,
    logo_only=True,
)
# html_logo = "_static/img/Oktoberfest.svg"


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Options for HTMLHelp output ---------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "spectrumfundamentalsdoc"

# -- Options for LaTeX output ------------------------------------------

latex_elements = {
    # The paper size ("letterpaper" or "a4paper").
    #
    # "papersize": "letterpaper",
    # The font size ("10pt", "11pt" or "12pt").
    #
    # "pointsize": "10pt",
    # Additional stuff for the LaTeX preamble.
    #
    # "preamble": "",
    # Latex figure (float) alignment
    #
    # "figure_align": "htbp",
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "SpectrumFundamentals.tex",
        "SpectrumFundamentals Documentation",
        author,
        "manual",
    ),
]

# -- Options for manual page output ------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        master_doc,
        "SpectrumFundamentals",
        "SpectrumFundamentals Documentation",
        [author],
        1,
    )
]

autodoc_typehints = "description"


# -- Options for Texinfo output ----------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "SpectrumFundamentals",
        "SpectrumFundamentals Documentation",
        author,
        "SpectrumFundamentals",
        "One line description of project.",
        "Miscellaneous",
    ),
]

html_css_files = [
    "custom_cookietemple.css",
]
# -- Options for intersphinx mappings ----------------------------------

intersphinx_mapping = dict(
    matplotlib=("https://matplotlib.org/stable/", None),
    numpy=("https://numpy.org/doc/stable/", None),
    pandas=("https://pandas.pydata.org/pandas-docs/stable/", None),
    python=("https://docs.python.org/3", None),
    scipy=("https://docs.scipy.org/doc/scipy/", None),
    seaborn=("https://seaborn.pydata.org/", None),
    sklearn=("https://scikit-learn.org/stable/", None),
)


# module path filter to create direct links to sources for autogenerated docs
# according to https://gist.github.com/flying-sheep/b65875c0ce965fbdd1d9e5d0b9851ef1


def get_obj_module(qualname):
    """Get a module/class/attribute and its original module by qualname."""
    modname = qualname
    classname = None
    attrname = None
    while modname not in sys.modules:
        attrname = classname
        modname, classname = modname.rsplit(".", 1)

    # retrieve object and find original module name
    if classname:
        cls = getattr(sys.modules[modname], classname)
        modname = cls.__module__
        obj = getattr(cls, attrname) if attrname else cls
    else:
        obj = None

    return obj, sys.modules[modname]


def get_linenos(obj):
    """Get an object’s line numbers."""
    try:
        lines, start = inspect.getsourcelines(obj)
    except TypeError:  # obj is an attribute or None
        return None, None
    else:
        return start, start + len(lines) - 1


project_dir = Path(__file__).parent.parent  # project/docs/conf.py/../.. → project/
github_url = "https://github.com/{github_user}/{github_repo}/tree/{github_version}".format_map(html_context)


def modurl(qualname):
    """Get the full GitHub URL for some object’s qualname."""
    obj, module = get_obj_module(qualname)
    path = Path(module.__file__).relative_to(project_dir)
    start, end = get_linenos(obj)
    fragment = f"#L{start}-L{end}" if start and end else ""
    return f"{github_url}/{path}{fragment}"


# html_context doesn’t apply to autosummary templates ☹
# and there’s no way to insert filters into those templates
# so we have to modify the default filters
DEFAULT_FILTERS["modurl"] = modurl
