from os.path import join, dirname, realpath, isfile
from sublime import HIDDEN, PERSISTENT, load_settings, cache_path
import subprocess, os, glob, re

class Line:

  # A digit is one-three numbers, with an optional floating point part,
  # and maybe a % sign, and maybe surrounded by whitespace.
  DIGIT = '\s*\d{1,3}(\.\d*)?%?\s*'

  # Three digits is three digits, with commas between.
  THREE_DIGITS = DIGIT + ',' + DIGIT + ',' + DIGIT

  # Four digits is three digits (which we save for later),
  # and then a comma and then the fourth digit.
  FOUR_DIGITS = '(' + THREE_DIGITS + '),' + DIGIT

  HEX_REGEXP = '#((?:[0-9a-fA-F]{3}){1,2}(?![0-9a-fA-F]+))'
  RGB_REGEXP = 'rgb\(' + THREE_DIGITS + '\)'
  RGBA_REGEXP = 'rgba\(' + FOUR_DIGITS + '\)'
  HSL_REGEXP = 'hsl\(' + THREE_DIGITS + '\)'
  HSLA_REGEXP = 'hsla\(' + FOUR_DIGITS + '\)'

  def __init__(self, view, region, file_id):
    self.view     = view
    self.region   = region
    self.file_id  = file_id
    self.settings = load_settings("GutterColor.sublime-settings")
    self.text     = self.view.substr(self.region)

  def has_color(self):
    """Returns True/False depending on whether the line has a color in it"""
    return True if self.color() else False

  def color(self):
    """Returns the color in the line, if any."""
    if self.hex_color():
      return self.hex_color()
    if self.rgb_color():
      return self.rgb_color()
    if self.rgba_color():
      return self.rgba_color()
    if self.hsl_color():
      return self.hsl_color()
    return self.hsla_color()

  def hex_color(self):
    """Returns the color in the line, if any hex is found."""
    matches = re.search(Line.HEX_REGEXP, self.text)
    if matches:
      return matches.group(0)

  def rgb_color(self):
    """Returns the color in the line, if any rgb is found."""
    matches = re.search(Line.RGB_REGEXP, self.text)
    if matches:
      return matches.group(0)

  def rgba_color(self):
    """Returns the color in the line, if any rgba is found."""
    matches = re.search(Line.RGBA_REGEXP, self.text)
    if matches:
      return 'rgb(' + matches.group(1) + ')'

  def hsl_color(self):
    """Returns the color in the line, if any hsl is found."""
    matches = re.search(Line.HSL_REGEXP, self.text)
    if matches:
      return matches.group(0)

  def hsla_color(self):
    """Returns the color in the line, if any rgba is found."""
    matches = re.search(Line.HSLA_REGEXP, self.text)
    if matches:
      return 'hsl(' + matches.group(1) + ')'


  def icon_path(self):
    """Returns the absolute path to the icons"""
    return join(cache_path(), 'GutterColor', '%s.png' % self.color())

  def relative_icon_path(self):
    """The relative location of the color icon"""
    return "Cache/GutterColor/%s.png" % (self.color())

  def add_region(self):
    """Add the icon to the gutter"""
    self.create_icon()
    self.view.add_regions(
      "gutter_color_%s" % self.region.a,
      [self.region],
      "gutter_color",
      self.relative_icon_path(),
      HIDDEN | PERSISTENT
    )

  def erase_region(self):
    """Remove icon from the gutter"""
    self.view.erase_regions("gutter_color_%s" % self.region.a)

  def create_icon(self):
    paths = [
      "/usr/bin/convert",
      "/usr/local/bin"
    ]

    paths.extend(glob.glob('/usr/local/Cellar/imagemagick/*/bin'))
    paths.extend(os.environ['PATH'].split(":"))
    paths.extend(self.settings.get("convert_path"))

    convert_path = None
    for path in paths:
      if os.path.isfile(path+"/convert") and os.access(path+"/convert", os.X_OK):
        convert_path = path+"/convert"
        break

    """Create the color icon using ImageMagick convert"""
    script = "\"%s\" -units PixelsPerCentimeter -type TrueColorMatte -channel RGBA " \
      "-size 32x32 -alpha transparent xc:none " \
      "-fill \"%s\" -draw \"circle 15,16 8,10\" png32:\"%s\"" % \
      (convert_path, self.color(), self.icon_path())
    if not isfile(self.icon_path()):
        pr = subprocess.Popen(script,
          shell = True,
          stdout = subprocess.PIPE,
          stderr = subprocess.PIPE,
          stdin = subprocess.PIPE)
        (result, error) = pr.communicate()
