
"""
Dedicated to getting the results you intend from your graql queries
"""


def check_response_length(response, min_length=None, max_length=None):
    """
    Throws runtime errors if the response doesn't return a number of elements within the prescribed range
    :param response:
    :param min_length:
    :param max_length:
    :return:
    """
    if (min_length is not None) and (len(response) < min_length):
        raise RuntimeError(("Grakn server response has length {}, but the minimum should have been {}. If using match, "
                            "insert, check that the \"match\" on it's own returns at least one combination of variables"
                            ".").format(len(response), min_length))
    elif (max_length is not None) and (len(response) > max_length):
        raise RuntimeError(("Grakn server response shows that {} insertions were made, but the maximum should have "
                            "been {}. If using match, insert, check that the \"match\" on it's own returns at the "
                            "desired number of combinations of variables.").format(len(response), max_length))
    elif min_length is None and max_length is None:
        raise RuntimeError("No bounds set on response length")
