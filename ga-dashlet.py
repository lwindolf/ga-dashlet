#!/usr/bin/env python
"""Transparent "dashlet" rendering Google Analytics data."""

import httplib2
import argparse
import cairo
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import GLib, Gtk, Gdk
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client import client, file, tools

def get_service(api_name, api_version, scope, key_file_location):
  """Get a service that communicates to a Google API.

  Args:
    api_name: The name of the api to connect to.
    api_version: The api version to connect to.
    scope: A list auth scopes to authorize for the application.
    key_file_location: The path to a valid service account JSON key file.

  Returns:
    A service that is connected to the specified API.
  """

  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      key_file_location, scopes=scope)

  # Build the service object.
  service = build(api_name, api_version, credentials=credentials)

  return service


def get_first_profile_id(service):
  # Use the Analytics service object to get the first profile id.

  # Get a list of all Google Analytics accounts for this user
  accounts = service.management().accounts().list().execute()

  if accounts.get('items'):
    # Get the first Google Analytics account.
    account = accounts.get('items')[0].get('id')

    # Get a list of all the properties for the first account.
    properties = service.management().webproperties().list(
        accountId=account).execute()

    if properties.get('items'):
      # Get the first property id.
      property = properties.get('items')[0].get('id')

      # Get a list of all views (profiles) for the first property.
      profiles = service.management().profiles().list(
          accountId=account,
          webPropertyId=property).execute()

      if profiles.get('items'):
        # return the first view (profile) id.
        return profiles.get('items')[0].get('id')

  return None


def get_results(service, profile_id):
  results = {}
  results['week'] = service.data().ga().get(
      ids='ga:' + profile_id,
      start_date='7daysAgo',
      end_date='today',
      metrics='ga:pageviews,ga:adsenseRevenue').execute()
  results['yesterday'] = service.data().ga().get(
      ids='ga:' + profile_id,
      start_date='yesterday',
      end_date='yesterday',
      metrics='ga:pageviews,ga:adsenseRevenue').execute()
  results['today'] = service.data().ga().get(
      ids='ga:' + profile_id,
      start_date='today',
      end_date='today',
      metrics='ga:pageviews,ga:adsenseRevenue').execute()
  return results

def ga_auth():
  key_file_location = 'client_secrets.json'
  service = get_service('analytics', 'v3', ['https://www.googleapis.com/auth/analytics.readonly'], key_file_location)
  profile = get_first_profile_id(service)
  return (service, profile)

def ga_fetch(service, profile):
  return get_results(service, profile)

class MyWin (Gtk.Window):
  def __init__(self):
    super(MyWin, self).__init__()
    self.set_position(Gtk.WindowPosition.CENTER)

    self.set_size_request(300, 70)
    self.set_border_width(10)
    self.restore_position()

    self.screen = self.get_screen()
    self.visual = self.screen.get_rgba_visual()
    if self.visual != None and self.screen.is_composited():
        self.set_visual(self.visual)
    else:
        print("Sorry, your screen is not composite! Transparency won't work.")

    self.set_app_paintable(True)
    self.connect("draw", self.area_draw)
    self.connect("window-state-event", self.window_state_event_cb)

    self.show_all()
    self.get_window().set_decorations(Gdk.WMDecoration.BORDER)
    self.get_window().set_type_hint(Gdk.WindowTypeHint.UTILITY)

    (self.service, self.profile) = ga_auth()
    self.update(None)
    GLib.timeout_add_seconds(30, self.update, None)

  def get_config_file(self):
    path = GLib.build_pathv('/', (GLib.get_user_config_dir(), 'ga-dashlet', None))
    GLib.mkdir_with_parents(path, 0700)
    return GLib.build_filenamev((path, 'settings.ini'))

  def restore_position(self):
    k = GLib.KeyFile.new()
    k.load_from_file(self.get_config_file(), GLib.KeyFileFlags.NONE)
    self.x = k.get_integer('window', 'x')
    self.y = k.get_integer('window', 'y')
    self.move(self.x, self.y)

  def save_position(self, x, y):
    k = GLib.KeyFile.new()
    k.set_integer('window', 'x', x)
    k.set_integer('window', 'y', y)
    k.save_to_file(self.get_config_file())

  def window_state_event_cb(self, widget, event):
    (x, y) = self.get_window().get_position()
    if self.x != x or self.y != y:
       self.x = x
       self.y = y
       self.save_position(x, y)

  def update(self, user_data):
    self.data = ga_fetch(self.service, self.profile)
    Gtk.Widget.queue_draw_area(self, 0, 0, 300, 70)
    return True

  def area_draw(self, widget, cr):
    cr.set_source_rgba(.2, .2, .2, 0.5)
    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)

    # Draw text + numbers
    cr.select_font_face("Monospace",
      cairo.FONT_SLANT_NORMAL,
      cairo.FONT_WEIGHT_NORMAL);
    cr.set_source_rgba(1, 1, 1, 1)
    cr.set_font_size(11);
    cr.move_to(12, 20);
    cr.show_text(self.data['today'].get('profileInfo').get('profileName'))

    cr.set_source_rgba(0.9, 0.9, 0.9, 1)
    cr.move_to(18, 38);
    cr.show_text("Today      %6s Views %03.2f EUR" % (
                self.data['today'].get('rows')[0][0],
          float(self.data['today'].get('rows')[0][1])))
    cr.move_to(18, 52);
    cr.show_text("Yesterday  %6s Views %03.2f EUR" % (
                self.data['yesterday'].get('rows')[0][0], 
          float(self.data['yesterday'].get('rows')[0][1])))
    cr.move_to(18, 66);
    cr.show_text("Last 7days %6s Views %03.2f EUR" % (
                self.data['week'].get('rows')[0][0],
          float(self.data['week'].get('rows')[0][1])))

if __name__ == '__main__':
  import signal
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  MyWin()
  Gtk.main()

# ex:ts=4:et:
