def output_as_str(string_like):
    if string_like is not None and type(string_like) != str:  # pylint: disable=unidiomatic-typecheck
        return string_like.decode('utf-8')
    else:
        return string_like
