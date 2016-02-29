#!/usr/bin/python

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
import signal
import os
import time
from gi.repository import GObject as gobject
import urllib2
import json
import gerrit_client
import settings
import sys


def get_last_build():
    req = urllib2.Request(settings.BVT_JOB)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    job_data = json.loads(s)
    build_numbers = [build["number"] for build in job_data["builds"]]
    return max(build_numbers)

def bvt_health():
    last_bvt = get_last_build()
    test_job_url = settings.BVT_TEST_JOB.format(settings.RELEASE, last_bvt)
    req = urllib2.Request(test_job_url)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    job_data = json.loads(s)
    return job_data['result']

def is_bvt_ok():
    if bvt_health() == 'FAILURE':
        return False
    return True


class SystemTray(object):

    def __init__(self):
        self.indicator = appindicator.Indicator.new(settings.APPINDICATOR_ID, os.path.abspath('green.png'), appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu({}))
        self.set_icon()
        gobject.timeout_add_seconds(settings.POLLING_INTERVAL, self.set_icon)
        gtk.main()

    def build_menu(self, active_reviews):
        menu = gtk.Menu()
        for review in active_reviews.keys():
            item_review = gtk.MenuItem(active_reviews[review])
            item_review.connect('activate', self.open_url, review)
            menu.append(item_review)
        item_quit = gtk.MenuItem('Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def quit(self, source):
        gtk.main_quit()
        sys.exit()

    def open_url(self, source, url):
        self.indicator.set_icon(os.path.abspath('grey.png'))
        os.system('python -m webbrowser -t "{0}"'.format(url))

    def choose_icon(self, active_reviews):
        if not is_bvt_ok():
            return 'red.png'
        if active_reviews:
            return 'orange.png'
        return 'green.png'

    def set_icon(self):
        active_reviews = gerrit_client.get_not_reviewed_patches(settings.gerrit_account_name, settings.reviews_url, settings.SKIP_LOWER_THAN)
        self.indicator.set_menu(self.build_menu(active_reviews))
        icon = self.choose_icon(active_reviews)
        self.indicator.set_icon(os.path.abspath(icon))
        return True

if __name__ == "__main__":
    SystemTray()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()
