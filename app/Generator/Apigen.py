import os
import urllib

class Apigen():
	dump_path = ""
	docgenerator_path = ""
	docgenerator_apigen_file = ""
		
	def initialize(self):
		self.docgenerator_apigen_file = os.path.join(self.docgenerator_path, "apigen.phar")

		if (os.path.isfile(self.docgenerator_apigen_file) == False):
			urllib.urlretrieve("http://apigen.org/apigen.phar", self.docgenerator_apigen_file)

	def get_command(self, repository_entry_path, doc_entry_path):
		return "php " + self.docgenerator_apigen_file + " generate " + " -s " + repository_entry_path + "  -d " + doc_entry_path
		