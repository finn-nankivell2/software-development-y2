from .modulebase import GameModule


def _verify_class(class_type, *required_methods):
	not_implemented = [m for m in required_methods if m not in dir(class_type)]
	if not_implemented:
		methods_names = ", ".join(not_implemented)
		msg = f"Methods not implemented for {class_type.__name__}: [{methods_names}]"
		raise NotImplementedError(msg)


class _BaseModule(GameModule):
	_REQUIRED_METHODS = []

	def verify(self):
		t = type(self) if type(self) != type else self
		_verify_class(t, *self._REQUIRED_METHODS)


class BaseSpriteManager(_BaseModule):
	IDMARKER = "sprites"
	_REQUIRED_METHODS = ["new", "get", "add_layer", "purge", "update"]

	def news(self, *sprites):
		for s in sprites:
			self.new(s)

	def add_layers(self, *layers):
		for x in layers:
			self.add_layer(x)

	def gets(self, *layer_names):
		ext = []
		for x in layer_names:
			ext.extend(self.get(x))
		return ext


class BaseLoopManager(_BaseModule):
	IDMARKER = "loop"
	_REQUIRED_METHODS = ["run", "stop"]


__all__ = [BaseLoopManager.__name__, BaseSpriteManager.__name__]


def test_UNIT_baseclass_notimplemented():

	class DerivedLoop(BaseLoopManager):
		pass

	try:
		DerivedLoop.verify(DerivedLoop)
	except NotImplementedError:
		pass  # Expected behaviour
	else:
		raise AssertionError("Implementation check failed")


def test_UNIT_baseclass_implemented():

	class DerivedLoop(BaseLoopManager):

		def run(self):
			pass

		def stop(self):
			pass

	DerivedLoop.verify(DerivedLoop)
