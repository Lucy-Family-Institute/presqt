# Configuration file for the Sphinx docs builder.
#
# This file only contains a selection of the most common options. For a full
# list see the docs:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# docs root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------
import sphinx_rtd_theme

project = 'PresQT'
copyright = '2019, ndlib'
author = 'Center For Research Computing'


# -- General configuration ---------------------------------------------------
master_doc = 'index'
# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_rtd_theme',
    'sphinxcontrib.httpdomain'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the docs for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

# from http://jack.rosenth.al/hacking-docutils.html#external-links-in-new-tabs
# from sphinx.writers.html import HTMLTranslator
# class PatchedHTMLTranslator(HTMLTranslator):
#    def visit_reference(self, node):
#       if node.get('newtab') or not (node.get('target') or node.get('internal')
#          or 'refuri' not in node):
#             node['target'] = '_blank'
#             super().visit_reference(node)
#
# def setup(app):
#     app.set_translator('html', PatchedHTMLTranslator)

from sphinx.writers.html import HTMLTranslator
from docutils import nodes
from docutils.nodes import Element

class PatchedHTMLTranslator(HTMLTranslator):
    def visit_reference(self, node: Element) -> None:
        atts = {'class': 'reference'}
        if node.get('internal') or 'refuri' not in node:
            atts['class'] += ' internal'
        else:
            atts['class'] += ' external'
            # ---------------------------------------------------------
            # Customize behavior (open in new tab, secure linking site)
            atts['target'] = '_blank'
            atts['rel'] = 'noopener noreferrer'
            # ---------------------------------------------------------
        if 'refuri' in node:
            atts['href'] = node['refuri'] or '#'
            if self.settings.cloak_email_addresses and atts['href'].startswith('mailto:'):
                atts['href'] = self.cloak_mailto(atts['href'])
                self.in_mailto = True
        else:
            assert 'refid' in node, \
                'References must have "refuri" or "refid" attribute.'
            atts['href'] = '#' + node['refid']
        if not isinstance(node.parent, nodes.TextElement):
            assert len(node) == 1 and isinstance(node[0], nodes.image)
            atts['class'] += ' image-reference'
        if 'reftitle' in node:
            atts['title'] = node['reftitle']
        if 'target' in node:
            atts['target'] = node['target']
        self.body.append(self.starttag(node, 'a', '', **atts))

        if node.get('secnumber'):
            self.body.append(('%s' + self.secnumber_suffix) %
                             '.'.join(map(str, node['secnumber'])))

def setup(app):
    app.set_translator('html', PatchedHTMLTranslator)

