from . import Apigen

class FactoryGenerator(object):
	generators = {"apigen": Apigen.Apigen()}

	@staticmethod
	def get_instance(generator):
		return FactoryGenerator.generators[generator]
