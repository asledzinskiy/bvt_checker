from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
import signal
import os
import time
from gi.repository import GObject as gobject
import urllib2
import json
import gerrit_client

APPINDICATOR_ID = 'myappindicator'
RELEASE = '8.0'
BVT_JOB = 'https://product-ci.infra.mirantis.net/job/{}.test_all/api/json'.format(RELEASE)
BVT_TEST_JOB = 'https://product-ci.infra.mirantis.net/job/{0}.test_all/{1}/api/json'

def get_last_build():
    req = urllib2.Request(BVT_JOB)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    job_data = json.loads(s)
    build_numbers = [build["number"] for build in job_data["builds"]]
    return max(build_numbers)

def bvt_health():
    last_bvt = get_last_build()
    test_job_url = BVT_TEST_JOB.format(RELEASE, last_bvt)
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
        self.indicator = appindicator.Indicator.new(APPINDICATOR_ID, os.path.abspath('green.png'), appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        gobject.timeout_add_seconds(30, self.set_icon)
        gtk.main()

    def build_menu(self):
        menu = gtk.Menu()
        item_quit = gtk.MenuItem('Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_quit)
        menu.show_all()
        return menu

    def quit(self, source):
        gtk.main_quit()

    def choose_icon(self):
        if not is_bvt_ok():
            return 'red.png'
        if gerrit_client.get_not_reviewed_patches():
            return 'orange.png'
        return 'green.png'

    def set_icon(self):
        icon = self.choose_icon()
        self.indicator.set_icon(os.path.abspath(icon))
        return True

if __name__ == "__main__":
    SystemTray()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()

