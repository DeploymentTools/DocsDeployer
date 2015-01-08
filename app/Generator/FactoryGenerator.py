import Apigen

class FactoryGenerator(object):
	generators = {"apigen": Apigen.Apigen()}

	@staticmethod
	def getInstance(generator):
		return FactoryGenerator.generators[generator]
