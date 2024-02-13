from types import SimpleNamespace


class GameNamespace():

	def __init__(self):
		self._modules = []
		self._idmarkers = []
		self._alias_idmarkers = []

		self.globals = SimpleNamespace()  # Modules should put reexports here

	def add_module(self, module_type, args=[], use_name=True, **kwargs):
		req = [r for r in module_type.REQUIREMENTS if r not in self._idmarkers and r not in self._alias_idmarkers]
		if len(req) > 0:
			raise TypeError(f"Requirements not met for {module_type.__name__}: {', '.join(req)}")

		if module_type.IDMARKER in self._idmarkers:
			raise TypeError(f"Multiple modules with same idmarker: {module_type.IDMARKER}")

		m = module_type(self)
		m.create(*args, **kwargs)

		if use_name:
			self.__dict__[module_type.IDMARKER] = m

		self._modules.append(m)
		self._idmarkers.append(module_type.IDMARKER)
		self._alias_idmarkers.extend(module_type.ALIASES)

	def add_module_object(self, module_obj, use_name=True):
		if use_name:
			self.__dict__[module_obj.IDMARKER] = m

		self._modules.append(module_obj)
		self._idmarkers.append(module_obj.IDMARKER)
		self._alias_idmarkers.extend(module_obj.ALIASES)

	def add_modules(self, *args, use_name=True):
		for m, a in args:
			self.add_module(m, a, use_name=use_name)
