import logging
import unittest
import sys
import os

sys.path.append('app')
from app.Deployer import Deployer

logging.basicConfig(level = logging.DEBUG)

class TestBA(unittest.TestCase):
	deployer = False

	# default setup settings
	def test_setup_default_redmine_url_key_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("http://localhost:8888", self.deployer.setup['redmine']['url'])

	def test_setup_default_redmine_user_key_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("deployer", self.deployer.setup['redmine']['user'])

	def test_setup_default_redmine_apikey_key_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("???", self.deployer.setup['redmine']['apikey'])

	def test_setup_default_dumpath_key_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("./dumppath", self.deployer.setup['dumppath'])

	def test_setup_default_generator_key_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("apigen", self.deployer.setup['generator'])

	# default projects settings
	def test_projects_first_name_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("CodeGraph", self.deployer.projects[0]['name'])

	def test_projects_first_repo_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("https://github.com/bogdananton/PHP-CodeGraph", self.deployer.projects[0]['repo'])

	def test_projects_first_redmine_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("codegraph", self.deployer.projects[0]['redmine'])

	def test_projects_first_branch_is_set(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual("master", self.deployer.projects[0]['branch'])

	# config path
	def test_config_path_after_initialize_is_computed(self):
		self.deployer = Deployer()
		self.deployer.initialize()
		self.assertEqual(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir,  "config")), self.deployer.config_path)

	def test_default_config_path_is_false(self):
		self.deployer = Deployer()
		self.assertFalse(self.deployer.config_path)

	def test_when_config_is_not_false_then_dont_override_on_prepareConfigPath(self):
		self.deployer = Deployer()

		custom_path = "/home/deployer/dumppath_custom/"
		self.deployer.config_path = custom_path

		self.deployer.prepareConfigPath()
		self.assertEqual(custom_path, self.deployer.config_path)

	# make path
	def test_make_path_will_create_directory_if_not_found_and_return_true(self):
		path = "./sample_test_path/"

		if (os.path.isdir(path) == True):
			os.rmdir(path)

		self.deployer = Deployer()
		response = self.deployer.make_path(path)

		self.assertTrue(response)
		os.rmdir(path) # cleanup

	def test_make_path_will_not_create_directory_if_found_and_return_false(self):
		path = "./sample_test_path/"

		if (os.path.isdir(path) == False):
			os.mkdir(path)

		self.deployer = Deployer()
		response = self.deployer.make_path(path)

		self.assertFalse(response)
		os.rmdir(path) # cleanup

if __name__ == '__main__':
	unittest.main()
