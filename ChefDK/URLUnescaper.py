#!/usr/bin/python
"""URL Unescaper."""

import HTMLParser

from autopkglib import Processor

__all__ = ["URLUnescaper"]


class URLUnescaper(Processor):
  """URL Unescaper."""

  # pylint: disable=missing-docstring
  description = ("Unescape a coded URL.")
  input_variables = {
    "escaped_url": {
      "required": True,
      "description": "Escaped/coded URL."
    },
  }
  output_variables = {
    "url": {
      "description": "Unescaped URL."
    }
  }

  __doc__ = description

  def main(self):
    """Magic."""
    html_parser = HTMLParser.HTMLParser()
    unescaped = html_parser.unescape(self.env['escaped_url'])
    self.env['url'] = unescaped


if __name__ == "__main__":
  PROCESSOR = URLUnescaper()
  PROCESSOR.execute_shell()
