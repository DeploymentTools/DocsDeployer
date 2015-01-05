# pip install gitpython
# http://packages.python.org/GitPython/
from git import Repo

import git
import json
import os
import sys
import re
import urllib

class Deployer():
	errors = []
	projects = []
	setup = []
	config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir,  "config"))

	def __init__(self):
		self.load_configuration()
		self.run_diagnostics()
		pass

	def sync_repositories(self):
		self.halt_on_error()
		self.errors = []

		log_docgenerator_commands = ""
		
		# basic paths
		repo_path = os.path.join(self.setup['dumppath'], "repositories")
		if (os.path.isdir(repo_path) == False):
			os.mkdir(repo_path)

		doc_output_path = os.path.join(self.setup['dumppath'], "documentation")
		if (os.path.isdir(doc_output_path) == False):
			os.mkdir(doc_output_path)
		
		apigen_binary = self.sync_docgenerator()

		log_branches = []

		# sync projects
		for project in self.projects:
			repository_URL = project['repo']
			repository_entry_path = os.path.join(repo_path, project['name'])

			if (os.path.isdir(repository_entry_path)):
				repo = Repo(repository_entry_path)
				origin = repo.remotes.origin
				origin.fetch()
				origin.pull()
				repo.git.checkout(project['branch'])

			else:
				Repo.clone_from(repository_URL, repository_entry_path)
			pass

			# create doc project entry folder
			doc_entry_path = os.path.join(doc_output_path, project['name'])
			if (os.path.isdir(doc_entry_path) == False):
				os.mkdir(doc_entry_path)

			# generate
			docgenerator_command = "php " + apigen_binary + " generate " + " -s " + repository_entry_path + "  -d " + doc_entry_path
			log_docgenerator_commands += docgenerator_command + "\n"
			
			###############################################
			# uncomment to generate documentation
			os.system(docgenerator_command)
			###############################################

			repo = Repo(repository_entry_path)
			
			branches = repo.git.branch("-r").split("\n")
			
			headcommit = repo.heads
			for branch in headcommit:
				logentry = str(branch.log()[-1])
				log_branches.append({"project": project['name'], "branch": str(branch), "commit": logentry.split(' ')[1]})

		log_docgenerator_file = open(os.path.join(self.setup['dumppath'], 'docgenerator_commands.sh'), 'w')
		log_docgenerator_file.write(log_docgenerator_commands)

		log_branches_file = open(os.path.join(self.setup['dumppath'], 'project_branches.json'), 'w')
		log_branches_file.write(json.dumps(log_branches))

		pass

	def sync_docgenerator(self):
		docgenerator_path = os.path.join(self.setup['dumppath'], "docgenerators")
	
		if (os.path.isdir(docgenerator_path) == False):
			os.mkdir(docgenerator_path)

		# # method 1 - using repos and composer
		# docgenerator_apigen_path = os.path.join(self.setup['dumppath'], "docgenerators", "apigen")

		# if (os.path.isdir(docgenerator_apigen_path) == False):
		# 	os.mkdir(docgenerator_apigen_path)
		# 	Repo.clone_from("https://github.com/apigen/apigen.git", docgenerator_apigen_path)
		#
		# # download composer & composer update apigen
		# composer_path = os.path.join(docgenerator_apigen_path, "composer.phar")
		# if (os.path.isfile(composer_path) == False):
		# 	urllib.urlretrieve("https://getcomposer.org/composer.phar", composer_path)
		# 	os.system("cd " + docgenerator_apigen_path + " && php " + composer_path + " update")
		#
		# os.system("php " + os.path.join(docgenerator_apigen_path, "bin", "apigen") + " list")

		# method 2 - phar
		docgenerator_apigen_file = os.path.join(self.setup['dumppath'], "docgenerators", "apigen.phar")
		if (os.path.isfile(docgenerator_apigen_file) == False):
			urllib.urlretrieve("http://apigen.org/apigen.phar", docgenerator_apigen_file)
		
		# os.system("php " + docgenerator_apigen_file + " generate --source ... --destination ...")
		# sys.exit()
		return docgenerator_apigen_file

	def run_diagnostics(self):
		if (len(self.projects) == 0):
			self.errors.append("No projects found or config/projects.json file is corrupt.")
		else:
			project_names = []
			for project in self.projects:
				if (project.has_key('repo') == False):
					self.errors.append("Invalid project entry. Repo key must be set for all entries.")
			
				if (project.has_key('name') == False):
					self.errors.append("Invalid project entry. Name key must be set for all entries.")
				else:
					check_alphanum = re.findall('^[\w-]+$', project['name'])
					if ((bool(check_alphanum) and check_alphanum[0] == project['name']) == False):
						self.errors.append("Project names must contain only alphanumeric chars or dash. [" + project['name'] + "]")

					if project['name'] in project_names:
						self.errors.append("Project names must be unique. Duplicate found for [" + project['name'] + "]")

					project_names.append(project['name'])

				pass

		if (len(self.setup) == 0):
			self.errors.append("No setup found or config/setup.json file is corrupt.")
		else:
			if (self.setup.has_key('dumppath') == False):
				self.errors.append("No dump path key found. Create a dumppath entry in the config/setup.json file")
			else:
				if (os.path.isdir(self.setup['dumppath']) == False):
					self.errors.append("Incorrect dump path. Create a writable folder and point to it in the config/setup.json file")
				else:
					if (os.access(self.setup['dumppath'], os.W_OK) == False):
						self.errors.append("Read-only dump path. Create a writable folder and point to it in the config/setup.json file")

		self.halt_on_error()
		pass

	def halt_on_error(self):
		if (len(self.errors) > 0):
			print("\nErrors found:")
			for error in self.errors:
				print(" - " + error)
				pass
			print("\n")
			sys.exit()
		pass

	def load_configuration(self):
		projects_file_path = self.config_path + '/projects.json'
		setup_file_path = self.config_path + '/setup.json'

		if (os.path.isfile(projects_file_path)):
			try:
				self.projects = json.loads(open(projects_file_path, 'r').read())
			except Exception, e:
				pass

		if (os.path.isfile(setup_file_path)):
			try:
				self.setup = json.loads(open(setup_file_path, 'r').read())
			except Exception, e:
				pass

		pass
