def is_method_overided_in_subclass(method_name: str, sub_class, base_class) -> bool:
    """Define whether subclass override specified method
    Args:
        method_name: to be defined method name
        sub_class: to be defined  sub class
        base_class: to be defined base class
    Returns:
        True or False
    """
    assert issubclass(sub_class, base_class), "class %s is not subclass of class %s" % (
        sub_class,
        base_class,
    )
    this_method = getattr(sub_class, method_name)
    base_method = getattr(base_class, method_name)
    return this_method is not base_method


if __name__ == '__main__':
    class A:
        def test_method(self):
            pass


    class B(A):
        def test_method(self):
            pass

    print(is_method_overided_in_subclass(method_name="test_method", sub_class=B, base_class=A))
