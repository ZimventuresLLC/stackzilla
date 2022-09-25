from stackbot.attribute import StackBotAttribute


class Class:
    """ Parameters in this class are defined as class variables. """
    required_arg = StackBotAttribute(required=True, modify_rebuild=True)
    optional_arg = StackBotAttribute(required=False, modify_rebuild=False)
    dynamic_arg = StackBotAttribute(dynamic=True)
    default_int = StackBotAttribute(default=42)
    default_float = StackBotAttribute(default=88.0)
    default_string = StackBotAttribute(default='GREAT SCOTT!')


class Instance:
    """ The parameters in this class are defined in the constructor as instance variables. """
    def __init__(self):
        self.required_arg = StackBotAttribute(required=True, modify_rebuild=True)
        self.optional_arg = StackBotAttribute(required=False, modify_rebuild=False)
        self.dynamic_arg = StackBotAttribute(dynamic=True)
        self.default_int = StackBotAttribute(default=42)
        self.default_float = StackBotAttribute(default=88.0)
        self.default_string = StackBotAttribute(default='GREAT SCOTT!')


class ChildObject(Class):
    """ Make sure Parameter objects in a base class function correctly """
    def __init__(self):
        self.required_arg = 1234

class ListTest(Class):
    """Make sure that the required_arg can be of type List"""
    def __init__(self):
        self.required_arg = [1, 2, 3]


parameter_names = ['required_arg', 'optional_arg', 'dynamic_arg', 'default_int', 'default_float', 'default_string']


def test_basic_assignment():
    """Assign a value to the required_arg field and ensure it's saved."""
    for obj in [Class, Instance, ChildObject]:
        node = obj()
        node.required_arg = 123
        assert node.required_arg == 123

def test_class_hasattr():
    """ Ensure that hasattr works for class objects """
    for cls in [Class, ChildObject]:
        for arg in parameter_names:
            assert hasattr(cls, arg) is True

    # The InstanceObject class should NOT have the class variables defined
    for arg in parameter_names:
        assert hasattr(Instance, arg) is False

def test_class_flags():
    """Verify that class variable flags are property set."""
    assert Class.required_arg.required is True
    assert Class.optional_arg.required is False
    assert Class.dynamic_arg.dynamic is True
    assert Class.required_arg.modify_rebuild is True
    assert Class.optional_arg.modify_rebuild is False

def test_defaults():
    """Verify that default values work for both class and instance parameterss."""
    for cls in [Class, ChildObject]:
        node = cls()
        assert node.default_int == 42
        assert node.default_float == 88.0
        assert node.default_string == 'GREAT SCOTT!'

        # Modify the defaults and verify the new values take hold
        node.default_int = 4200
        node.default_float = 8800.0
        node.default_string = 'Thanks for all the fish.'

        assert node.default_int == 4200
        assert node.default_float == 8800.0
        assert node.default_string == 'Thanks for all the fish.'

def test_instance_hasattr():
    """ Verify that hasattr works for instantiated objects """
    for obj in [Class, Instance, ChildObject]:
        node = obj()
        for arg in parameter_names:
            assert hasattr(node, arg) is True

def test_lists():
    """Enure that the list attributes are set and fetched correctly."""
    obj = ListTest()
    assert(obj.required_arg == [1, 2, 3])
