# pip install gitpython
# http://packages.python.org/GitPython/
import git
from git import Repo
from redmine import Redmine

import json
from .Generator import FactoryGenerator

import json
import os
import sys
import re

class Deployer():
	errors = []
	projects = []
	setup = []
	generator = False
	log_docgenerator_commands = ""
	repo_path = ""
	doc_output_path = ""
	log_branches = {}
	report_template_html = ""
	ID_filter_active = True # will only select branches that start with a numeric ID followed by an underline sign
	config_path = False
	log_diff_files = {}

	def __init__(self):
		pass

	def initialize(self):
		self.prepareConfigPath()
		self.load_configuration()
		self.run_diagnostics()
		self.init_generator()
		self.load_report_template()
		pass

	def load_report_template(self):
		report_template_html_file = open(os.path.join(self.config_path, "template.html"), 'r+')
		self.report_template_html = report_template_html_file.read()
		report_template_html_file.close()

	def prepareConfigPath(self):
		if (self.config_path == False):
			self.config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir,  "config"))

	def get_dump_path(self):
		return self.setup['dumppath']

	def init_generator(self):
		docgenerator_path = os.path.join(self.get_dump_path(), "docgenerators")
		self.make_path(docgenerator_path)

		generator = FactoryGenerator.FactoryGenerator.get_instance(self.setup['generator'])
		generator.dump_path = self.get_dump_path()
		generator.docgenerator_path = docgenerator_path
		generator.initialize()
		self.generator = generator

		return True

	def make_path(self, path):
		if (os.path.isdir(path) == False):
			os.mkdir(path)
			return True
		return False

	def refresh_repository(self, project):
		path = self.get_repo_path(project)

		if (os.path.isdir(path)):
			repo = Repo(path)
			origin = repo.remotes.origin
			try:
				origin.fetch()
				origin.pull()
				repo.git.checkout(project['branch'])
			except Exception:
				pass
		else:
			Repo.clone_from(project['repo'], path)
		pass

	def extract_branches(self, project):
		repo = Repo(self.get_repo_path(project))
		headcommit = repo.heads

		entry = {"name": project["name"], "branch": project["branch"], "commit": "", "branches":[]}

		for branch in headcommit:
			logentry = str(branch.log()[-1])
			branch_name = str(branch)

			if (branch_name != project['branch']):
				if (self.ID_filter_active == False) or ((self.ID_filter_active == True) and (re.match(r"^#\d_", branch_name) is not None)):
					branch_entry = {}
					branch_entry["branch"] = branch_name
					branch_entry["commit"] = logentry.split(' ')[1]
					branch_entry["status"] = "unknown"
					branch_entry["author"] = "unknown"
					entry["branches"].append(branch_entry)
			else:
				entry["commit"] = logentry.split(' ')[1]

		self.log_branches[project["name"]] = entry

	def get_repos_path(self):
		return os.path.join(self.setup['dumppath'], "repositories")

	def get_repo_path(self, project):
		return os.path.join(self.get_repos_path(), project['name'])

	def get_docs_path(self):
		return os.path.join(self.setup['dumppath'], "documentation")

	def get_doc_path(self, project):
		return os.path.join(self.get_docs_path(), project['name'])

	def sync_repositories(self):
		self.halt_on_error()
		self.errors = []

		self.make_path(self.get_repos_path())
		self.make_path(self.get_docs_path())

		# sync projects
		for project in self.projects:
			self.refresh_repository(project)
			self.extract_branches(project)
			self.apply_redmine_filter_to_clear_branches(project)
			self.extract_diff_with_master_branch(project)

			# create doc project entry folder
			self.make_path(self.get_doc_path(project))

			# generate main documentation
			docgenerator_command = self.generator.get_command(self.get_repo_path(project), self.get_doc_path(project))
			os.system(docgenerator_command) # uncomment to generate documentation
			self.append_docgenerator_command(docgenerator_command)

		# save logs
		self.save_log_docgenerator_commands()
		self.save_log_branches()
		self.save_log_diff_files(project)
		self.generate_html_frontend()

	def append_docgenerator_command(self, command):
		self.log_docgenerator_commands += command + "\n"

	def save_log_docgenerator_commands(self):
		log_docgenerator_file = open(os.path.join(self.setup['dumppath'], 'docgenerator_commands.sh'), 'w')
		log_docgenerator_file.write(self.log_docgenerator_commands)
		log_docgenerator_file.close()

	def save_log_branches(self):
		log_branches_file = open(os.path.join(self.setup['dumppath'], 'project_branches.json'), 'w')
		log_branches_file.write(json.dumps(self.log_branches))
		log_branches_file.close()
	
	def save_log_diff_files(self, project):
		project_name = project['name']
		if project_name in self.log_diff_files:
			for branch_name in self.log_diff_files[project_name].keys():
				if len(self.log_diff_files[project_name][branch_name]) > 0:
					log_diff_file = open(os.path.join(self.setup['dumppath'], project_name+'_diff_files_'+branch_name+'.json'), 'w')
					log_diff_file.write(json.dumps(self.log_diff_files[project_name][branch_name]))
					log_diff_file.close()

	def generate_html_frontend(self):
		output_html = open(os.path.join(self.setup['dumppath'], 'index.html'), 'w')
		output_html.write(self.report_template_html.replace("[--BRANCHES--]", json.dumps(self.log_branches)))

	def run_diagnostics(self):
		if (len(self.projects) == 0):
			self.errors.append("No projects found or config/projects.json file is corrupt.")
		else:
			project_names = []
			for project in self.projects:
				if ('repo' not in project):
					self.errors.append("Invalid project entry. Repo key must be set for all entries.")
			
				if ("name" not in project):
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
			if ('dumppath' not in self.setup):
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
				f = open(projects_file_path, 'r')
				self.projects = json.loads(f.read())
				f.close()
			except Exception:
				pass

		if (os.path.isfile(setup_file_path)):
			try:
				f = open(setup_file_path, 'r')
				self.setup = json.loads(f.read())
				f.close()
			except Exception:
				pass
		pass
	def extract_diff_with_master_branch(self, project):
		# set detached head for each branch
		branch_to_compare = project['branch']
		project_name =project['name']
		repo = Repo(self.get_repo_path(project))
		# clean dirty files or work in progress (we should not have) and checkout to master branch
		repo.head.reset(index=True, working_tree=True)
		repo.git.checkout(branch_to_compare)
		head_commit = repo.head.commit
		self.log_diff_files[project_name] = {}

		for branch_info in self.log_branches[project_name]['branches']:
			diff_object = head_commit.diff(branch_info['commit'])
			self.log_diff_files[project_name][branch_info['branch']] = []

			for diff_added in diff_object.iter_change_type('M'):
				self.log_diff_files[project_name][branch_info['branch']].append(diff_added.a_blob.path)

	def apply_redmine_filter_to_clear_branches(self, project):
		no_error = True
		try:
			redmine = Redmine(self.setup['redmine']['url'], name = self.setup['redmine']['user'], passwd = self.setup['redmine']['password'])
			# redmine_project= redmine.project.get(project['redmine_project'])
			branches = []
			for branch_info in self.log_branches[project['name']]['branches']:
				# extract the corresponded issue id
				issue_id = re.match(r"^#(\d+)_", branch_info['branch']).group(1)
				issue = redmine.issue.get(issue_id)
				if issue.status.name.lower() !='closed':
					branch_info['status'] = issue.status.name.lower()
					branches.append(branch_info)
		except Exception:
			no_error = False
			pass
		
		# overwrite branches with the filtered one
		# can be risky
		# we can have zero valid branches  
		if no_error :
			self.log_branches[project['name']]['branches'] = branches
