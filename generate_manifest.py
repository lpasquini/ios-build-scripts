#!/usr/bin/python

from optparse import OptionParser
import shutil
import fileinput
import os
import sys
import glob
import subprocess
import plistlib
import urlparse
import string

parser = OptionParser()
parser.add_option('-f', '--app-bundle', action='store', dest='app_bundle', help='Path to app bundle')
parser.add_option('-a', '--archive-name', action='store', dest='archive_name', help='Legacy archive filename')
parser.add_option('-d', '--deployment-address', action='store', dest='deployment_address', help='Remote deployment path, where the app will eventually be hosted')
parser.add_option('-i', '--info-plist', action='store', dest='info_plist', default='Info.plist', help='Info.plist filename inside the application bundle (defaults to Info.plist)')

(options, args) = parser.parse_args()

if options.app_bundle == None:
	parser.error("Please specify the file path to the app bundle.")
elif options.deployment_address == None:
	parser.error("Please specify the deployment address.")
elif options.archive_name == None:
	parser.error("Please specify the filename of the legacy archive.")

class IPAGenerator(object):
	"Generate index.html"
	def generate_html(self, app_name):
		HTML_FILENAME = 'index.html'
		index_file = open(HTML_FILENAME, 'w')
		index_file.write(self.template(app_name))
		return HTML_FILENAME

	"Generate manifest by parsing values from the app's Info.plist"
	def generate_manifest(self, app_name):
		info_plist_filepath = os.path.join(options.app_bundle, options.info_plist)
		info_plist_xml_filename = 'info_plist.xml'
		# Use plutil to ensure that we are dealing with XML rather than the binary format
		subprocess.Popen('plutil -convert xml1 -o ' + info_plist_xml_filename + ' ' + info_plist_filepath, shell=True).wait()
		info_plist_xml_file = open(info_plist_xml_filename, 'r')
		app_plist = plistlib.readPlist(info_plist_xml_file)
		os.remove(info_plist_xml_filename)
		MANIFEST_FILENAME = 'manifest.plist'
		manifest_plist = {
				'items' : [
					{
						'assets' : [
							{
								'kind' : 'software-package',
								'url' : urlparse.urljoin(options.deployment_address, app_name + '.ipa'),
								}
							],
						'metadata' : {
							'bundle-identifier' : app_plist['CFBundleIdentifier'],
							'bundle-version' : app_plist['CFBundleVersion'],
							'kind' : 'software',
							'title' : app_plist['CFBundleName'],
							}
						}
					]
				}
		plistlib.writePlist(manifest_plist, MANIFEST_FILENAME)
		return MANIFEST_FILENAME

	"Template from http://github.com/HunterHillegas/iOS-BetaBuilder"
	def template(self, app_name):
		template_html = """
		<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
		<html xmlns="http://www.w3.org/1999/xhtml">
		<head>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
		<title>[BETA_NAME] - Beta Release</title>
		<style type="text/css">
		body {background:#fff;margin:0;padding:0;font-family:arial,helvetica,sans-serif;text-align:center;padding:10px;color:#333;font-size:16px;}
		#container {width:300px;margin:0 auto;}
		h1 {margin:0;padding:0;font-size:14px;}
		p {font-size:13px;}
		.link {background:#ecf5ff;border-top:1px solid #fff;border:1px solid #dfebf8;margin-top:.5em;padding:.3em;}
		.link a {text-decoration:none;font-size:15px;display:block;color:#069;}
		
		</style>
		</head>
		<body>
		
		<div id="container">
		
		<h1>iOS 4.0 Users:</h1>
		
		<div class="link"><a href="itms-services://?action=download-manifest&url=[DEPLOYMENT_PATH]">Tap Here to Install<br />[BETA_NAME]<br />On Your Device</a></div>
		
		<p><strong>Link didn't work?</strong><br />
		Make sure you're visiting this page on your device, not your computer.</p>
		
		<p><strong>On a version of iOS before 4.0?</strong><br />
		Reload this page in your computer browser and download a zipped archive and provisioning profile here:
		</p>
		
		<div class="link"><a href="[BETA_ARCHIVE_FILENAME]">[BETA_NAME]<br />Archive w/ Provisioning Profile</a></div>
		
		</div>
		
		</body>
		</html>
		"""
		TEMPLATE_PLACEHOLDER_NAME = '[BETA_NAME]'
		TEMPLATE_PLACEHOLDER_DEPLOYMENT_PATH = '[DEPLOYMENT_PATH]'
		TEMPLATE_PLACEHOLDER_ARCHIVE_FILENAME = '[BETA_ARCHIVE_FILENAME]'
		template_html = string.replace(template_html, TEMPLATE_PLACEHOLDER_NAME, app_name)
		template_html = string.replace(template_html, TEMPLATE_PLACEHOLDER_DEPLOYMENT_PATH, options.deployment_address)
		template_html = string.replace(template_html, TEMPLATE_PLACEHOLDER_ARCHIVE_FILENAME, options.archive_name)
		return template_html

generator = IPAGenerator()
app_name = os.path.splitext(options.app_bundle)[0]
html_filename = generator.generate_html(app_name)
manifest_filename = generator.generate_manifest(app_name)
