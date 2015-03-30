import os
import sys

if sys.version_info < (3, 0):
	import urllib
else:
	import urllib.request

class Apigen():
	dump_path = ""
	docgenerator_name = "apigen"
	docgenerator_path = ""
	docgenerator_apigen_file = ""
		
	def initialize(self):
		self.docgenerator_apigen_file = os.path.join(self.docgenerator_path, self.docgenerator_name)

		if (os.path.isfile(self.docgenerator_apigen_file) == False):
			if sys.version_info < (3, 0):
				urllib.urlretrieve("http://apigen.org/apigen.phar", self.docgenerator_apigen_file)
			else:
				urllib.request.urlretrieve("http://apigen.org/apigen.phar", self.docgenerator_apigen_file)

	def get_command(self, repository_entry_path, doc_entry_path):
		return "php " + self.docgenerator_apigen_file + " generate " + " -s " + repository_entry_path + "  -d " + doc_entry_path
		